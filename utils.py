import heapq
import re
from collections import OrderedDict
from typing import Optional

from fastapi import Request
from sqlalchemy.orm import Session

from db import ActiveModel, GroupModel, StatsModel
from schemas import GroupSchema
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


def serialize_stats(db: Session, selection: dict) -> OrderedDict:
    data = db.query(StatsModel, GroupModel).join(GroupModel).order_by(
        StatsModel.group_id).where(StatsModel.group_id.in_(selection.keys()))

    context = OrderedDict()
    for i, content in enumerate(data):
        stats, group = content
        if stats.group_id not in context:
            heap = []
            heapq.heapify(heap)
            context[stats.group_id] = {
                'group_name': group.name,
                'cost': selection[stats.group_id][1],
                'data': heap,
            }

        click_rub = stats.cost // stats.clicks if stats.clicks else stats.cost
        item = (stats.date, i, {'click_rub': click_rub,
                                'date': stats.date.strftime('%d %B %y'),
                                'post_name': stats.post_name,
                                'cost_prev': stats.cost,
                                'new_follows': stats.new_follows,
                                'clicks': stats.clicks})

        heapq.heappush(context[stats.group_id]['data'], item)
        if len(context[stats.group_id]['data']) > MAX_PLACEMENTS:
            heapq.heappop(context[stats.group_id]['data'])

    for i in context.values():
        i['data'].sort()

    return context


def serialize_active(db: Session, selection: dict) -> OrderedDict:
    active_data = db.query(ActiveModel, GroupModel).join(GroupModel).order_by(
        ActiveModel.group_id).where(ActiveModel.group_id.in_(selection.keys()))

    active_items = OrderedDict()
    for active, group in active_data:
        active_items[active.group_id] = (
            group.name, active.date.strftime('%d %B %y'))

    return active_items


def render_template(request: Request,
                    message: Optional[str] = '',
                    context: Optional[dict] = None,
                    no_data: Optional[list] = None,
                    active: Optional[OrderedDict] = None) -> None:
    return templates.TemplateResponse(
        'index.html',
        {'request': request, 'context': context, 'no_data': no_data,
         'active': active, 'message': message})
