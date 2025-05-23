from celery import Celery

# Broker and (optionally) result backend
BROKER_URL   = 'redis://localhost:6380/0'
BACKEND_URL  = 'redis://localhost:6380/1'


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
