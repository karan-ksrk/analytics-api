from api.db.config import DATABASE_URL
from fastapi import APIRouter, Depends, HTTPException, Query
from api.db.session import get_session
from sqlmodel import Session, select
from timescaledb.utils import get_utc_now
from api.events.models import EventModel
from timescaledb.hyperfunctions import time_bucket
from sqlalchemy import func, Case
from typing import List

from .models import (
    EventModel,
    EventBucketSchema,
    EventCreateSchema,
)
router = APIRouter()

DEFAULT_LOOKUP_PAGES = [
    "/", "/about", "/pricing", "/contact",
    "/blog", "/products", "/login", "/signup",
    "/dashboard", "/settings"
]

# list


@router.get("/", response_model=List[EventBucketSchema])
def read_events(
    duration: str = Query(default="1 day"),
    pages: List = Query(default=None),
    session: Session = Depends(get_session),

):

    os_case = Case(
        (EventModel.user_agent.ilike('%windows%'), 'Windows'),
        (EventModel.user_agent.ilike('%macintosh%'), 'MacOs'),
        (EventModel.user_agent.ilike('%iphone%'), 'iOS'),
        (EventModel.user_agent.ilike('%android%'), 'Android'),
        (EventModel.user_agent.ilike('%linux%'), 'Linux'),
        else_="Other"
    ).label('operating_system')

    bucket = time_bucket(duration, EventModel.time)
    lookup_pages = pages if isinstance(pages, list) and len(
        pages) > 0 else DEFAULT_LOOKUP_PAGES
    query = (
        select(
            bucket.label('bucket'),
            os_case,
            EventModel.page.label('page'),
            func.avg(EventModel.duration).label('avg_duration'),
            func.count().label('count')
        )
        .where(
            EventModel.page.in_(lookup_pages)
        )
        .group_by(
            bucket,
            os_case,
            EventModel.page,
        )
        .order_by(
            bucket,
            os_case,
            EventModel.page
        )
    )
    results = session.exec(query).fetchall()
    return results


# create
@router.post("/", response_model=EventModel)
def create_events(
        payload: EventCreateSchema,
        session: Session = Depends(get_session)):
    # a bunch of items in a table
    data = payload.model_dump()  # payload -> dict -> pydantic
    obj = EventModel.model_validate(data)
    session.add(obj)
    session.commit()
    session.refresh(obj)
    return obj


# get detail
@router.get("/{event_id}", response_model=EventModel)
def get_events(
        event_id: int,
        session: Session = Depends(get_session)):
    query = select(EventModel).where(EventModel.id == event_id)
    obj = session.exec(query).first()
    if not obj:
        raise HTTPException(status_code=404, detail="Event not found")
    return obj
