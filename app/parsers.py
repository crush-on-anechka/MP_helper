import re
from datetime import date, timedelta
from typing import Optional

import requests
from db.models import ActiveModel, Cookies, StatsModel
from db.schemas import ActiveSchema, StatsSchema
from settings import HEADERS, PARAMS, STATUSES, URL, data
from sqlalchemy.orm import Session


def get_stats(db: Session, start_date: date,
              end_date: Optional[date] = None) -> (list[StatsModel], dict):

    end_date = end_date or date.today()
    cookies, hash_curl = get_cookies(db)

    data['start_time'] = str(start_date).replace('-', '')
    data['end_time'] = str(end_date).replace('-', '')
    data['hash'] = hash_curl

    response = requests.post(url=URL, params=PARAMS, cookies=cookies,
                             headers=HEADERS, data=data)

    try:
        decoded_response = response.text.encode('latin1').decode('cp1251')
    except UnicodeEncodeError:
        raise

    split_response = decoded_response.split('\n')

    objects, groups = [], {}

    for col in split_response[1:]:
        col = col.split(';')
        if col[0] == 'Всего':
            break

        group_id = col[-11]
        groups[group_id] = col[7].encode('UTF-8')

        cur_obj = {
            'date': col[0],
            'post_name': col[5].encode('UTF-8'),
            'group_id': group_id,
            'followers': col[-10],
            'reach_daily': col[-9],
            'cost': col[-8],
            'clicks': col[-7],
            'new_follows': col[-6],
            'reach_all': col[-5],
            'reach_followers': col[-4],
            'likes': col[-3],
            'shares': col[-2],
            'comments': col[-1],
        }

        obj = StatsSchema(**cur_obj)
        objects.append(obj.dict())

    stats_instances = [StatsModel(**obj) for obj in objects]

    return stats_instances, groups


def get_selection(db: Session, request_url: str) -> dict:
    data = {'al': '1'}

    try:
        for param in request_url.split('&')[1:]:
            key, val = param.split('=')
            data[key] = val.replace('%2C', ',')

        params = {'act': 'community_search'}
        params['ad_id'] = data.pop('ad_id')
    except (ValueError, KeyError):
        raise

    cookies, _ = get_cookies(db)

    response = requests.post(url=URL, params=params, cookies=cookies,
                             headers=HEADERS, data=data).text

    re_patterns = {
        'group_name': r'exchange_comm_name\\".{,50}',
        'group_idx': r'stats-\d+',
        'prices': r'человек<\\/td>.{,200}<\\/b> руб.',
        'reach_post': r'nowrap.{,200} \\/ ',
        'reach_daily': r' \\/ .{,200}человек',
    }

    group_name = [i[21:i.find('<\/a>')] for i in re.findall(
        re_patterns['group_name'], response)]

    group_idx = extract_digits(re_patterns['group_idx'], response)
    prices = extract_digits(re_patterns['prices'], response)
    reach_post = extract_digits(re_patterns['reach_post'], response)
    reach_daily = extract_digits(re_patterns['reach_daily'], response)

    return {i: (n, p, cp, cd) for i, n, p, cp, cd in zip(
        group_idx, group_name, prices, reach_post, reach_daily)}


def get_cookies(db: Session) -> (dict, str):
    data = db.query(Cookies).first().__dict__
    cookies = {
        'remixsid': data.get('remixsid'),
        'remixnsid': data.get('remixnsid'),
    }
    hash_curl = data.get('hash')

    return cookies, hash_curl


def get_active(db: Session, status: str) -> (list[ActiveModel], dict):
    params = {'act': 'overview'}
    data = {
        'act': 'overview',
        'al': '1',
        'part': '1',
        'status': status,
    }

    cookies, _ = get_cookies(db)

    response = requests.post(url=URL, params=params, cookies=cookies,
                             headers=HEADERS, data=data).text

    group_name = [i[15:i.find('<\/a>')] for i in re.findall(
        r'"group_link\\" >.{,50}', response)]

    prices = extract_digits(r'Цена:.{,200}<\\/b> руб.', response)

    if status == STATUSES['active']:
        group_idx, post_date = handle_active(response)
    elif status == STATUSES['pending']:
        group_idx, post_date = handle_pending(response)

    objects, groups = [], {}

    for i, n, pd, pr in zip(group_idx, group_name, post_date, prices):

        groups[i] = n

        cur_obj = {
            'date': pd,
            'group_id': i,
            'cost': pr,
        }

        obj = ActiveSchema(**cur_obj)
        objects.append(obj.dict())

    active_instances = [ActiveModel(**obj) for obj in objects]

    return active_instances, groups


def handle_active(response: str) -> (list[int], list[date]):
    re_patterns = {
        'group_idx_active': r'stats-\d+',
        'post_date_active': r'Опубликована:<\\/span>\S+',
    }

    group_idx = extract_digits(re_patterns['group_idx_active'], response)

    post_date = []

    for sub in re.findall(re_patterns['post_date_active'], response):
        yt = 'вчера' in sub
        post_date.append(date.today() - timedelta(days=yt))

    return group_idx, post_date


def handle_pending(response: str) -> (list[int], list[date]):
    re_patterns = {
        'group_idx_pending': r'deleteRequest\(\d+',
        'post_date_pending': r'Будет опубликована:<\\/span><br>.{,20} в ',
    }

    group_idx = extract_digits(re_patterns['group_idx_pending'], response)

    post_date = []

    for sub in re.findall(re_patterns['post_date_pending'], response):
        td, tm, yt = 'сегодня' in sub, 'завтра' in sub, 'вчера' in sub
        if td or tm or yt:
            post_date.append(
                date.today() + timedelta(days=tm) - timedelta(days=yt))
        else:
            d, m, y = re.search(r'\d{1,2} \D{3} \d{4}', sub)[0].split()
            post_date.append(date(int(y), convert_month(m), int(d)))

    return group_idx, post_date


def extract_digits(pattern: str, response: str) -> list[int]:
    return [int(re.sub(r'\D', '', i)) for i in re.findall(pattern, response)]


def convert_month(month: str) -> int:
    match = {'янв': 1, 'фев': 2, 'мар': 3, 'апр': 4, 'май': 5, 'июн': 6,
             'июл': 7, 'авг': 8, 'сен': 9, 'окт': 10, 'ноя': 11, 'дек': 12}
    return match[month]
