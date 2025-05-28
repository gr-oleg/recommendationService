from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from model import Recommender
import requests

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

rec = Recommender()

ORDER_SERVICE_URL = "http://56.228.34.106/order/getAll"
ITEM_SERVICE_URL = "http://16.171.137.58/item/getAll"

@app.on_event("startup")
def load_all():
    try:
        rec.load()
        rec.items = requests.get(ITEM_SERVICE_URL).json()
        rec.items_by_id = {str(x["id"]): x for x in rec.items}
    except Exception as e:
        print("Startup error_:", e)

@app.post("/train")
def train_model():
    try:
        orders_raw = requests.get(ORDER_SERVICE_URL).json()
        items = requests.get(ITEM_SERVICE_URL).json()
        orders = []
        for order in orders_raw:
            # idItems = "[27,28,26,32,33,36,39]"
            for iid in eval(order["idItems"]):
                orders.append({"userId": str(order["idUser"]), "itemId": str(iid)})
        rec.train(orders, items)
        return {"status": "model trained", "orders_used": len(orders)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/recommend/popular")
def popular(
    n: int = Query(5, ge=1, le=20),
    category: str = None,
    sex: str = None
):
    try:
        return {"popular_items": rec.popular(n=n, filter_category=category, filter_sex=sex)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/recommend/{user_id}")
def recommend(
    user_id: int,
    n: int = Query(5, ge=1, le=20),
    category: str = None,
    sex: str = None
):
    try:
        rec.load()
        rec.items = requests.get(ITEM_SERVICE_URL).json()
        rec.items_by_id = {str(x["id"]): x for x in rec.items}
        return {"recommended_items": rec.recommend(user_id, n=n, filter_category=category, filter_sex=sex)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/recommend/content/{user_id}")
def content_based(user_id: int, n: int = Query(5, ge=1, le=20)):
    try:
        return {"content_based_items": rec.content_based_for_user(user_id, n=n)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))