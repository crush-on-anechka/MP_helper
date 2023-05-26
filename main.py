from datetime import date

from fastapi import Depends, FastAPI, Form, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from db import ActiveModel, Cookies, StatsModel, get_db
from parsers import get_active, get_selection, get_stats
from settings import START_YEAR, STATUSES, templates
from utils import (extract_cookies, get_group_instances, serialize_active,
                   serialize_stats, write_to_db)

app = FastAPI()


@app.get('/', response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse(
        'index.html', {'request': request, 'context': {}})


@app.post('/update_stats')
def update_stats_handler(request: Request, db: Session = Depends(get_db)):
    last_date: date = db.query(
        StatsModel.date).order_by(StatsModel.date.desc()).limit(1).scalar()

    try:
        stats_instances, groups = get_stats(db=db, start_date=last_date)
    except UnicodeEncodeError:
        message = 'load stats failed: did you forget to load initial data?'
        return templates.TemplateResponse(
            'index.html', {'request': request, 'message': message})

    if not stats_instances:
        message = 'load stats failed: did you forget to update cookies?'
        return templates.TemplateResponse(
            'index.html', {'request': request, 'message': message})

    active_instances, active_groups = get_active(db, STATUSES['active'])
    pending_instances, pending_groups = get_active(db, STATUSES['pending'])

    groups.update(active_groups)
    groups.update(pending_groups)

    group_instances = get_group_instances(groups)
    db.query(StatsModel).filter_by(date=last_date).delete()
    db.query(ActiveModel).delete()
    write_to_db(db=db, stats=stats_instances, groups=group_instances,
                active=active_instances + pending_instances)

    return templates.TemplateResponse(
        'index.html', {'request': request, 'message': 'stats are up to date'})


@app.post('/load_stats')
def load_stats_handler(request: Request, db: Session = Depends(get_db)):
    stats_instances, groups = [], {}
    current_year = date.today().year

    for year in range(START_YEAR, current_year + 1, 2):
        start_date = f'{year}0101'
        end_date = f'{year + 2}0101'
        cur_stats, cur_groups = get_stats(db, start_date, end_date)
        if not cur_stats:
            message = 'load stats failed: did you forget to update cookies?'
            return templates.TemplateResponse(
                'index.html', {'request': request, 'message': message})
        stats_instances.extend(cur_stats)
        groups.update(cur_groups)

    group_instances = get_group_instances(groups)
    write_to_db(db=db, stats=stats_instances, groups=group_instances)

    return templates.TemplateResponse(
        'index.html', {'request': request, 'message': 'stats loaded'})


@app.post('/analyze', response_class=HTMLResponse)
def analyze_handler(request: Request, url: str = Form(),
                    db: Session = Depends(get_db)):

    selection = get_selection(db, url)

    if not selection:
        message = 'oops.. did you forget to update cookies?'
        return templates.TemplateResponse(
            'index.html', {'request': request, 'message': message})

    context = serialize_stats(db, selection)
    active_items = serialize_active(db, selection)

    no_data = [(k, v[0]) for k, v in selection.items()
               if k not in context and k not in active_items]

    return templates.TemplateResponse(
        'index.html',
        {'request': request, 'context': context,
         'no_data': no_data, 'active': active_items})


@app.post('/update_cookies')
def update_cookies_handler(request: Request, curl: str = Form(),
                           db: Session = Depends(get_db)):

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
        message = 'something went wrong, check curl'
        return templates.TemplateResponse(
            'index.html', {'request': request, 'message': message})

    db.query(Cookies).delete()
    cookies = Cookies(remixsid=remixsid, remixnsid=remixnsid, hash=curl_hash)
    db.add(cookies)
    db.commit()

    return templates.TemplateResponse(
        'index.html',
        {'request': request, 'message': 'cookies are up to date'})
