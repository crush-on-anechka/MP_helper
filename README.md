# MP_helper

MP_helper is designed and created for my personal use, it helps me run ads for my workshop via VK.com's market platform by parsing, storing, processing and delivering data and thereby providing better performance of my ads.  

## stack
- [FastApi]  
- [SQLAlchemy]  
- [PostgreSQL]  

## preparing
- go to the project folder in terminal and run:  
        - `python3 -m venv venv` to set up your virtual environment  
        - `. venb/bin/activate` to activate it  
        - `pip install -r requirements.txt` to install necessary libraries  
- create a `.env file` and fill it up using the following schema:  
        - DB_NAME=database_name  
        - POSTGRES_USER=user  
        - POSTGRES_PASSWORD=password  
        - UNION_ID=123456789 (your VK user id)  
        - DATABASE_URL=postgresql://{user}:{password}@0.0.0.0:{port}/{database_name}  


## starting
- make sure your docker is up  
- from the root folder in terminal run:  
        - `docker-compose up -d` to set up the database  
- from the 'app/db' folder run:  
        - `alembic upgrade heads` to set up database tables  
- from the 'app' folder run:  
        - `uvicorn main:app --reload` and you are ready to go!  

## using
- go to https://vk.com/adsmarket?act=export_stats, open your dev tools (cmd+option+U), press GET DATA blue button, find most recent 'adsmarket' line in sources tab, click right button and COPY AS CURL  
- go to http://127.0.0.1:8000, paste the copied data into 'put your request as curl here' form and press 'update cookies'. You will have to update cookies once a day  
- now you can load your stats. This may take some time (±2 minutes). This will initially fill up the database, you don't need to do it every time you use the app, only unless you killed the db volume  
- press 'update stats' to obtain active placements. Use it whenever you feel like it's time to refresh data  
- now you can place your ads. Once you get the selection of groups, copy the url (as you would normally do - via the address bar), paste it into 'put your selection link here' form in the app and press 'analyze'  

## features
- ##### show pending total
    see the amount of money blocked for pending ads divided up by days
- ##### show performance
    see performance stats for each of the ad creatives for specified time frames

   [FastApi]: <https://fastapi.tiangolo.com/>
   [SQLAlchemy]: <https://www.sqlalchemy.org/>
   [PostgreSQL]: <https://www.postgresql.org/>
