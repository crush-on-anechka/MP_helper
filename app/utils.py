import re
from typing import Optional

from fastapi import Request
from sqlalchemy.orm import Session

from db.models import ActiveModel, GroupModel, StatsModel
from db.schemas import GroupSchema
from settings import MAX_PLACEMENTS, templates


def get_group_instances(groups: dict) -> list[GroupModel]:
    groups = [GroupSchema(id=i, name=n).dict() for i, n in groups.items()]
    group_instances = [GroupModel(**group) for group in groups]
    return group_instances


def write_to_db(db: Session, stats: list[StatsModel], groups: list[GroupModel],
                active: list[ActiveModel] = None) -> None:
    for group in groups:
        db.merge(group)
    db.flush()
    db.add_all(stats)
    if active:
        db.add_all(active)
    db.commit()


def extract_cookies(pattern: str, curl: str) -> str:
    match = re.search(pattern, curl)[0]
    anchors = ['remixsid=', 'remixnsid=', 'hash=']
    for item in anchors:
        match = match.replace(item, '')
    return match


def get_context(db: Session, selection: dict) -> dict:
    data = db.query(StatsModel, GroupModel).join(GroupModel).order_by(
        StatsModel.group_id).order_by(StatsModel.date.desc()).where(
            StatsModel.group_id.in_(selection.keys()))

    context = {}
    for stats, group in data:
        if stats.group_id not in context:
            context[stats.group_id] = {
                'group_name': group.name,
                'cost': selection[stats.group_id][1],
                'reach': f'{selection[stats.group_id][2] // 1000} / '
                         f'{selection[stats.group_id][3] // 1000}',
                'data': [],
            }

        if len(context[stats.group_id]['data']) < MAX_PLACEMENTS:
            cl_rub = stats.cost // stats.clicks if stats.clicks else stats.cost
            reach_rub = (stats.cost * 1000 // stats.reach_all
                         if stats.reach_all else stats.cost)
            item = {'click_rub': cl_rub,
                    'date': stats.date.strftime('%d %B %y'),
                    'post_name': stats.post_name,
                    'cost_prev': stats.cost,
                    'new_follows': stats.new_follows,
                    'clicks': stats.clicks,
                    'reach': stats.reach_all,
                    'reach_rub': reach_rub}

            context[stats.group_id]['data'].append(item)

    return context


def render_template(request: Request,
                    message: Optional[str] = '',
                    context: Optional[dict] = None,
                    pending: Optional[dict] = None,
                    performance: Optional[list] = None,
                    active: Optional[dict] = None) -> None:
    return templates.TemplateResponse(
        'index.html',
        {'request': request, 'context': context, 'pending': pending,
         'performance': performance, 'active': active, 'message': message})
