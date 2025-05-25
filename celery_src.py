import os
from celery import Celery
from dotenv import load_dotenv

load_dotenv()

# Broker and (optionally) result backend
BROKER_URL   = os.getenv("BROKER_URL")
BACKEND_URL  = os.getenv("BACKEND_URL")


celery_app = Celery(
    'dstasks',
    broker=BROKER_URL,
    backend=BACKEND_URL,
)

celery_app.conf.update(
    enable_utc=True,            # treat all times internally as UTC
    timezone='UTC',             # explicitly set the working timezone
    task_serializer='json',
    result_serializer='json',
    accept_content=['json'],
    include=["app.tasks.sms_tasks"],
)


# Import your tasks AFTER celery_app is defined
# import tasks.x_tasks


celery_app.autodiscover_tasks(["app.tasks"])
