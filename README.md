# Recommendation Platform — Python мікросервіси + NGINX (API Gateway)

## Структура

- recommendation_service/ — рекомендації (FastAPI, порт 8001)
- chat_service/ — чат-асистент (FastAPI, порт 8003)
- stats_service/ — аналітика (FastAPI, порт 8004)
- nginx/nginx.conf — NGINX як API Gateway (порт 8080)

## Як запускати

1. **Встановити залежності для кожного сервісу:**
   ```bash
   cd recommendation_service && pip install -r requirements.txt && cd ..
   cd chat_service && pip install -r requirements.txt && cd ..
   cd stats_service && pip install -r requirements.txt && cd ..
   ```

2. **Запускати кожен сервіс у окремому терміналі:**
   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8001  # recommendation_service
   uvicorn main:app --host 0.0.0.0 --port 8003  # chat_service
   uvicorn main:app --host 0.0.0.0 --port 8004  # stats_service
   ```

3. **Встановити NGINX (якщо не встановлений):**
   ```bash
   sudo apt update
   sudo apt install nginx
   ```

4. **Запустити NGINX із цією конфігурацією:**
   ```bash
   sudo nginx -c /path/to/nginx/nginx.conf
   ```

5. **Тепер всі API доступні через єдиний порт:**
   - http://localhost:8080/recommend/...
   - http://localhost:8080/chat/...
   - http://localhost:8080/stats/...

## Пояснення

- NGINX працює як єдиний вхід (API Gateway)
- Мікросервіси можна масштабувати окремо
- Легко розгортається навіть на слабких VPS (наприклад, AWS t2.micro)