import os

from dotenv import load_dotenv
from fastapi.templating import Jinja2Templates

load_dotenv()

START_YEAR = 2015
MAX_PLACEMENTS = 5

MESSAGES = {
    'success_stats_update': 'stats are up to date',
    'success_stats_load': 'stats successfully loaded',
    'success_cookies': 'cookies are up to date',
    'failed_init': 'task failed: did you forget to load initial data?',
    'failed_cookies': 'task failed: did you forget to update cookies?',
    'failed_no_url': 'task failed: enter url',
    'failed_invalid_url': 'task failed: check url',
    'failed_no_curl': 'task failed: enter curl',
    'failed_invalid_curl': 'task failed: check curl',
    'failed_date': 'task failed, check date format',
}

URL = 'https://vk.com/adsmarket'

HEADERS = {'X-Requested-With': 'XMLHttpRequest'}

PARAMS = {
    'act': 'get_export_stats',
    'union_id': os.environ.get('UNION_ID'),
}

STATUSES = {
    'pending': '1',
    'active': '3',
}

data = {
    'al': '1',
    'export_method': '2',
    'grouping_exchange': '4',
}

templates = Jinja2Templates(directory="templates")

DATABASE_URL = os.environ.get('DATABASE_URL')
