from api.db.config import DATABASE_URL
from fastapi import APIRouter, Depends, HTTPException, Query
from api.db.session import get_session
from sqlmodel import Session, select
from timescaledb.utils import get_utc_now
from api.events.models import EventModel
from timescaledb.hyperfunctions import time_bucket
from sqlalchemy import func
from typing import List

from .models import (
    EventModel,
    EventBucketSchema,
    EventCreateSchema,
)
router = APIRouter()

DEFAULT_LOOKUP_PAGES = ["/about", "/contact", "/pages", "pricing"]

# list


@router.get("/", response_model=List[EventBucketSchema])
def read_events(
    duration: str = Query(default="1 day"),
    pages: List = Query(default=None),
    session: Session = Depends(get_session),

):
    bucket = time_bucket(duration, EventModel.time)
    lookup_pages = pages if isinstance(pages, list) and len(
        pages) > 0 else DEFAULT_LOOKUP_PAGES
    query = (
        select(
            bucket.label('bucket'),
            EventModel.page.label('page'),
            func.count().label('count')
        )
        .where(
            EventModel.page.in_(lookup_pages)
        )
        .group_by(
            bucket,
            EventModel.page,
        )
        .order_by(
            bucket,
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
