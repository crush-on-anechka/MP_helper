from datetime import date

from pydantic import BaseModel


class ModifiedModel(BaseModel):

    class Config:
        orm_mode = True


class GroupSchema(ModifiedModel):
    id: int
    name: str


class StatsSchema(ModifiedModel):
    date: date
    post_name: str
    group_id: int
    followers: int
    reach_daily: int
    cost: int
    clicks: int
    new_follows: int
    reach_all: int
    reach_followers: int
    likes: int
    shares: int
    comments: int


class ActiveSchema(ModifiedModel):
    date: date
    group_id: int
