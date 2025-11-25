- Run worker: 
```
celery -A app.celery_app.celery_app worker --loglevel=INFO
```

- Run app
```
uvicorn app.main:app --reload
```

