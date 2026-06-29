from apscheduler.schedulers.background import BackgroundScheduler

from .email_workflow_generation import create_email_workflow_job


def run():
    scheduler = BackgroundScheduler()
    # scheduler.add_job(create_email_workflow_job, "interval", seconds=60)
    scheduler.start()
