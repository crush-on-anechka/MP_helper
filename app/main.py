from datetime import date, datetime
from typing import Optional

from db.models import ActiveModel, Cookies, StatsModel
from db.session import get_db
from fastapi import Depends, FastAPI, Form, Request
from fastapi.responses import HTMLResponse
from parsers import get_active, get_selection, get_stats
from settings import MESSAGES, START_YEAR, STATUSES
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from utils import (extract_cookies, get_context, get_group_instances,
                   render_template, write_to_db)

app = FastAPI()
cache = set()
skipped = set()


@app.get('/', response_class=HTMLResponse)
def index(request: Request):
    return render_template(request=request)


@app.post('/update_stats')
def update_stats_handler(request: Request, db: Session = Depends(get_db)):
    last_date: date = db.query(
        StatsModel.date).order_by(StatsModel.date.desc()).limit(1).scalar()

    try:
        stats_instances, groups = get_stats(db=db, start_date=last_date)
    except UnicodeEncodeError:
        return render_template(
            request=request, message=MESSAGES['failed_init'])

    if not stats_instances:
        return render_template(
            request=request, message=MESSAGES['failed_cookies'])

    active_instances, active_groups = get_active(db, STATUSES['active'])
    pending_instances, pending_groups = get_active(db, STATUSES['pending'])

    groups.update(active_groups)
    groups.update(pending_groups)

    group_instances = get_group_instances(groups)
    db.query(StatsModel).filter_by(date=last_date).delete()
    db.query(ActiveModel).delete()
    write_to_db(db=db, stats=stats_instances, groups=group_instances,
                active=active_instances + pending_instances)

    return render_template(
        request=request, message=MESSAGES['success_stats_update'])


@app.post('/load_stats')
def load_stats_handler(request: Request, db: Session = Depends(get_db)):
    stats_instances, groups = [], {}
    current_year = date.today().year

    for year in range(START_YEAR, current_year + 1, 2):
        start_date = f'{year}0101'
        end_date = f'{year + 2}0101'
        cur_stats, cur_groups = get_stats(db, start_date, end_date)
        if not cur_stats:
            return render_template(
                request=request, message=MESSAGES['failed_cookies'])
        stats_instances.extend(cur_stats)
        groups.update(cur_groups)

    group_instances = get_group_instances(groups)
    db.query(StatsModel).delete()
    write_to_db(db=db, stats=stats_instances, groups=group_instances)

    return render_template(
        request=request, message=MESSAGES['success_stats_load'])


@app.post('/analyze', response_class=HTMLResponse)
def analyze_handler(request: Request, url: Optional[str] = Form(None),
                    db: Session = Depends(get_db)):
    if not url:
        return render_template(
            request=request, message=MESSAGES['failed_no_url'])

    try:
        selection = get_selection(db, url)
    except (KeyError, ValueError):
        return render_template(
            request=request, message=MESSAGES['failed_invalid_url'])

    if not selection:
        return render_template(
            request=request, message=MESSAGES['failed_cookies'])

    context = get_context(db, selection)

    active_data = db.query(ActiveModel).where(
        ActiveModel.group_id.in_(selection.keys()))
    active_items = [item.group_id for item in active_data]

    for group_idx, data in selection.items():
        if group_idx not in context:
            context[group_idx] = {
                'group_name': data[0],
                'cost': data[1],
                'reach': f'{data[2] // 1000} / {data[3] // 1000}',
                'data': None,
            }

    context = dict(sorted(context.items()))

    template = render_template(request=request, context=context, cache=cache,
                               active=active_items, skipped=skipped)

    cache.update(selection.keys())

    return template


@app.post('/update_cookies')
def update_cookies_handler(request: Request, curl: str = Form(None),
                           db: Session = Depends(get_db)):
    if not curl:
        return render_template(
            request=request, message=MESSAGES['failed_no_curl'])

    re_patterns = {
        'remixsid': r'remixsid=[^;]+',
        'remixnsid': r'remixnsid=[^;]+',
        'hash': r'hash=[^&]+',
    }

    try:
        remixsid = extract_cookies(re_patterns['remixsid'], curl)
        remixnsid = extract_cookies(re_patterns['remixnsid'], curl)
        curl_hash = extract_cookies(re_patterns['hash'], curl)
    except TypeError:
        return render_template(
            request=request, message=MESSAGES['failed_invalid_curl'])

    db.query(Cookies).delete()
    cookies = Cookies(remixsid=remixsid, remixnsid=remixnsid, hash=curl_hash)
    db.add(cookies)
    db.commit()

    return render_template(
        request=request, message=MESSAGES['success_cookies'])


@app.get('/pending', response_class=HTMLResponse)
def pending_total_handler(request: Request, db: Session = Depends(get_db)):
    active_instances, _ = get_active(db, STATUSES['active'])
    pending_instances, _ = get_active(db, STATUSES['pending'])

    pending = {}

    for item in active_instances + pending_instances:
        dt = item.date.strftime('%d %B %y')
        pending[dt] = pending.get(dt, 0) + item.cost

    pending = dict(sorted(pending.items()))

    return render_template(request=request, pending=pending)


@app.post('/performance')
def performance_handler(request: Request, start: str = Form(None),
                        db: Session = Depends(get_db)):
    try:
        dt = datetime.strptime(start, "%d%m%y").strftime('%d %B %y')
    except (TypeError, ValueError):
        return render_template(
            request=request, message=MESSAGES['failed_date'])

    today = date.today().strftime('%d %B %y')

    message = f'performance data for {dt} - {today}'

    performance = db.query(
        StatsModel.post_name,
        func.sum(StatsModel.clicks).label('clicks'),
        func.sum(StatsModel.cost).label('cost'),
        func.sum(StatsModel.reach_all).label('reach')
        ).where(StatsModel.date > dt).group_by(StatsModel.post_name)

    return render_template(request=request, message=message,
                           performance=performance)


@app.post('/clear_cache')
def clear_cache_handler(request: Request):
    global cache
    global skipped
    skipped.update(cache)
    cache = set()

    return render_template(
        request=request, message=MESSAGES['success_cache'])
