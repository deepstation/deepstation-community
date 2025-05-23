from app.library.sms_utils import send_sms_to
from celery_src import celery_app

@celery_app.task(queue="sms", rate_limit="1/s")
def send_sms_to_rate_limited_task(from_number: str, to_number: str, body: str):
    send_sms_to(from_number, to_number, body)