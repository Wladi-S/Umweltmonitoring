from apscheduler.schedulers.background import BackgroundScheduler
from initialize import update_data
from utils import train_and_update_forecast, fetch_and_prepare_data


def start_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        update_data, "interval", minutes=1, id="update_data_job", replace_existing=True
    )
    scheduler.add_job(
        train_and_update_forecast,
        "cron",
        minute=0,  # This ensures the job runs at the top of every hour
        id="forecast_job",
        replace_existing=True,
    )
    scheduler.start()
