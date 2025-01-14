import asyncio
import os
from typing import List, Optional

import uvicorn
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

import sql_app.models as models
import sql_app.schemas as schemas
import universities
from db import engine, get_db
from instrumentation.az_inject_instrumentation import inject_instrumentation
from instrumentation.get_instrumented_logger import get_instumented_logger
from instrumentation.with_instrumentation import with_instrumentation
from sql_app.repositories import ItemRepo, StoreRepo

app = FastAPI(
    title="Sample FastAPI Application",
    description="Sample FastAPI Application with Swagger and Sqlalchemy",
    version="1.0.0",
)

models.Base.metadata.create_all(bind=engine)
logger = get_instumented_logger(__name__)


@app.exception_handler(Exception)
def validation_exception_handler(request, err):
    base_error_message = f"Failed to execute: {request.method}: {request.url}"
    return JSONResponse(
        status_code=400, content={"message": f"{base_error_message}. Detail: {err}"}
    )


@app.post("/items", tags=["Item"], response_model=schemas.Item, status_code=201)
@with_instrumentation
async def create_item(item_request: schemas.ItemCreate, db: Session = Depends(get_db)):
    """
    Create an Item and store it in the database
    """

    db_item = ItemRepo.fetch_by_name(db, name=item_request.name)
    if db_item:
        raise HTTPException(status_code=400, detail="Item already exists!")

    return await ItemRepo.create(db=db, item=item_request)


@app.get("/items", tags=["Item"], response_model=List[schemas.Item])
@with_instrumentation
def get_all_items(name: Optional[str] = None, db: Session = Depends(get_db)):
    """
    Get all the Items stored in database
    """
    if name:
        items = []
        db_item = ItemRepo.fetch_by_name(db, name)
        items.append(db_item)
        return items
    else:
        return ItemRepo.fetch_all(db)


@app.get("/items/{item_id}", tags=["Item"], response_model=schemas.Item)
@with_instrumentation
def get_item(item_id: int, db: Session = Depends(get_db)):
    """
    Get the Item with the given ID provided by User stored in database
    """
    db_item = ItemRepo.fetch_by_id(db, item_id)
    if db_item is None:
        raise HTTPException(status_code=404, detail="Item not found with the given ID")
    return db_item


@app.delete("/items/{item_id}", tags=["Item"])
@with_instrumentation
async def delete_item(item_id: int, db: Session = Depends(get_db)):
    """
    Delete the Item with the given ID provided by User stored in database
    """
    db_item = ItemRepo.fetch_by_id(db, item_id)
    if db_item is None:
        raise HTTPException(status_code=404, detail="Item not found with the given ID")
    await ItemRepo.delete(db, item_id)
    return "Item deleted successfully!"


@app.put("/items/{item_id}", tags=["Item"], response_model=schemas.Item)
@with_instrumentation
async def update_item(
    item_id: int, item_request: schemas.Item, db: Session = Depends(get_db)
):
    """
    Update an Item stored in the database
    """
    db_item = ItemRepo.fetch_by_id(db, item_id)
    if db_item:
        update_item_encoded = jsonable_encoder(item_request)
        db_item.name = update_item_encoded["name"]
        db_item.price = update_item_encoded["price"]
        db_item.description = update_item_encoded["description"]
        db_item.store_id = update_item_encoded["store_id"]
        return await ItemRepo.update(db=db, item_data=db_item)
    else:
        raise HTTPException(status_code=400, detail="Item not found with the given ID")


@app.post("/stores", tags=["Store"], response_model=schemas.Store, status_code=201)
@with_instrumentation
async def create_store(
    store_request: schemas.StoreCreate, db: Session = Depends(get_db)
):
    """
    Create a Store and save it in the database
    """
    db_store = StoreRepo.fetch_by_name(db, name=store_request.name)
    print(db_store)
    if db_store:
        raise HTTPException(status_code=400, detail="Store already exists!")

    return await StoreRepo.create(db=db, store=store_request)


@app.get("/stores", tags=["Store"], response_model=List[schemas.Store])
@with_instrumentation
def get_all_stores(name: Optional[str] = None, db: Session = Depends(get_db)):
    """
    Get all the Stores stored in database
    """
    if name:
        stores = []
        db_store = StoreRepo.fetch_by_name(db, name)
        print(db_store)
        stores.append(db_store)
        return stores
    else:
        return StoreRepo.fetch_all(db)


@app.get("/stores/{store_id}", tags=["Store"], response_model=schemas.Store)
@with_instrumentation
def get_store(store_id: int, db: Session = Depends(get_db)):
    """
    Get the Store with the given ID provided by User stored in database
    """
    db_store = StoreRepo.fetch_by_id(db, store_id)
    if db_store is None:
        raise HTTPException(status_code=404, detail="Store not found with the given ID")
    return db_store


@app.delete("/stores/{store_id}", tags=["Store"])
@with_instrumentation
async def delete_store(store_id: int, db: Session = Depends(get_db)):
    """
    Delete the Item with the given ID provided by User stored in database
    """
    db_store = StoreRepo.fetch_by_id(db, store_id)
    if db_store is None:
        raise HTTPException(status_code=404, detail="Store not found with the given ID")
    await StoreRepo.delete(db, store_id)
    return "Store deleted successfully!"


@app.get("/universities/", tags=["University"])
@with_instrumentation
def get_universities() -> dict:
    """
    Return the List of universities for some random countries in sync way
    """
    data: dict = {}
    data.update(universities.get_all_universities_for_country("turkey"))
    data.update(universities.get_all_universities_for_country("india"))
    data.update(universities.get_all_universities_for_country("australia"))
    return data


@app.get("/universities/async", tags=["University"])
@with_instrumentation
async def get_universities_async() -> dict:
    """
    Return the List of universities for some random countries in async way
    """
    data: dict = {}
    await asyncio.gather(
        universities.get_all_universities_for_country_async("turkey", data),
        universities.get_all_universities_for_country_async("india", data),
        universities.get_all_universities_for_country_async("australia", data),
    )
    return data



if __name__ == "__main__":
    load_dotenv()
    inject_instrumentation(app)
    log_config = uvicorn.config.LOGGING_CONFIG
    log_config["formatters"]["access"][
        "fmt"
    ] = '[trace_id=%(otelTraceID)s span_id=%(otelSpanID)s] %(levelprefix)s %(client_addr)s - "%(request_line)s" %(status_code)s"'
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=int(os.environ.get("APP_PORT", "8000")),
        log_config=log_config,
    )
