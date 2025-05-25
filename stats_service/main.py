from fastapi import FastAPI, HTTPException
import requests
from collections import Counter

app = FastAPI()

# Замінити адреси, якщо order/item сервіси живуть на інших портах або мають інші ендпоінти
ORDER_SERVICE_URL = "http://56.228.34.106/order/getAll"
ITEM_SERVICE_URL = "http://16.171.137.58/item/getAll"

@app.get("/stats")
def stats():
    try:
        # Підрахунок топ-товарів і користувачів
        item_counter = Counter()
        user_counter = Counter()
        orders_raw = requests.get(ORDER_SERVICE_URL).json()
        for order in orders_raw:
            for iid in eval(order["idItems"]):
                item_counter[str(iid)] += 1
                user_counter[str(order["idUser"])] += 1
        top_items = item_counter.most_common(10)
        top_users = user_counter.most_common(10)
        items = requests.get(ITEM_SERVICE_URL).json()
        items_by_id = {str(x["id"]): x for x in items}
        top_items_info = [
            {**items_by_id[iid], "count": count}
            for iid, count in top_items if iid in items_by_id
        ]
        return {
            "top_items": top_items_info,
            "top_users": [{"userId": uid, "orders": c} for uid, c in top_users]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))