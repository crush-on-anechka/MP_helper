import os

from dotenv import load_dotenv
from fastapi.templating import Jinja2Templates

load_dotenv()

START_YEAR = 2015
MAX_PLACEMENTS = 4

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
