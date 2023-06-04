
initial migration (no alembic.ini file yet):  
- run `alembic init migrations`  
- go to /migrations folder and add this code to the env.py file:  
> from dotenv import load_dotenv  
from db import Base  
load_dotenv()  
config.set_main_option('sqlalchemy.url', os.environ.get('DATABASE_URL'))  
target_metadata = Base.metadata  

create migration:  
    alembic revision --autogenerate -m 'comment'  

apply migration:  
    alembic upgrade heads  
