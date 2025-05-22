import os
import pandas as pd
from surprise import Dataset, Reader, SVD, dump
from collections import Counter, defaultdict

class Recommender:
    def __init__(self, model_path="model.pkl"):
        self.model_path = model_path
        self.model = None
        self.orders_df = None
        self.user_item_counter = None
        self.items = []
        self.items_by_id = {}
        self.trained = False

    def train(self, orders, items):
        # orders: [{"userId": ..., "itemId": ...}]
        # items: [{"id": ..., "name": ..., ...}]
        self.items = items
        self.items_by_id = {str(x["id"]): x for x in items}

        df = pd.DataFrame(orders)
        # Групуємо, рахуємо кількість покупок кожного item користувачем (implicit рейтинг)
        df["userId"] = df["userId"].astype(str)
        df["itemId"] = df["itemId"].astype(str)
        rating_df = df.groupby(["userId", "itemId"]).size().reset_index(name="rating")
        self.orders_df = rating_df.copy()
        self.user_item_counter = Counter(zip(df["userId"], df["itemId"]))

        # Навчаємо SVD
        reader = Reader(rating_scale=(1, rating_df["rating"].max()))
        data = Dataset.load_from_df(rating_df[["userId", "itemId", "rating"]], reader)
        trainset = data.build_full_trainset()
        self.model = SVD(n_factors=50, n_epochs=30, reg_all=0.05, random_state=42)
        self.model.fit(trainset)
        dump.dump(self.model_path, algo=self.model)
        self.trained = True

    def load(self):
        if os.path.exists(self.model_path):
            _, self.model = dump.load(self.model_path)
            self.trained = True

    def recommend(self, user_id, n=5, filter_category=None, filter_sex=None):
        user_id = str(user_id)
        if not self.trained:
            raise Exception("Model not trained")
        # Вибираємо тільки ті товари, які ще не купував цей користувач
        bought = set(self.orders_df[self.orders_df["userId"] == user_id]["itemId"]) if self.orders_df is not None else set()
        candidate_items = [str(x["id"]) for x in self.items if str(x["id"]) not in bought]
        # Фільтр по категорії/статі
        if filter_category:
            candidate_items = [iid for iid in candidate_items if self.items_by_id[iid].get("category") == filter_category]
        if filter_sex:
            candidate_items = [iid for iid in candidate_items if self.items_by_id[iid].get("sex") == filter_sex]

        # Якщо юзер новий — повертаємо популярне по фільтру
        if len(bought) == 0:
            return self.popular(n=n, filter_category=filter_category, filter_sex=filter_sex)
        # Scoring
        pred = [(iid, self.model.predict(user_id, iid).est) for iid in candidate_items]
        pred.sort(key=lambda x: x[1], reverse=True)
        return [self.items_by_id[iid] for iid, _ in pred[:n]]

    def popular(self, n=5, filter_category=None, filter_sex=None):
        # Підрахунок по всім замовленням
        cnt = defaultdict(int)
        for row in self.orders_df.itertuples():
            iid = row.itemId
            if filter_category and self.items_by_id[iid].get("category") != filter_category:
                continue
            if filter_sex and self.items_by_id[iid].get("sex") != filter_sex:
                continue
            cnt[iid] += int(row.rating)
        top_items = sorted(cnt.items(), key=lambda x: x[1], reverse=True)
        return [self.items_by_id[iid] for iid, _ in top_items[:n]]

    def content_based_for_user(self, user_id, n=5):
        # Як приклад: рекомендує товари з тієї ж категорії, що й попередні покупки юзера
        user_id = str(user_id)
        if self.orders_df is None or user_id not in set(self.orders_df["userId"]):
            return self.popular(n=n)
        bought = self.orders_df[self.orders_df["userId"] == user_id]["itemId"].tolist()
        cats = [self.items_by_id[iid]["category"] for iid in bought if iid in self.items_by_id]
        if not cats:
            return self.popular(n=n)
        top_cat = Counter(cats).most_common(1)[0][0]
        candidate_items = [iid for iid in self.items_by_id if self.items_by_id[iid]["category"] == top_cat]
        # Вибираємо ті, яких юзер ще не купував
        candidate_items = [iid for iid in candidate_items if iid not in bought]
        return [self.items_by_id[iid] for iid in candidate_items[:n]]