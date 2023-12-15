from django.apps import AppConfig
from apscheduler.schedulers.background import BackgroundScheduler
from core.cron import move_log_to_archive
from django.conf import settings

class CoreConfig(AppConfig):
    name = 'core'
    def ready(self):
        # if not settings.DEBUG:  # 개발 환경이 아닐 때만 스케줄러를 실행합니다.
            scheduler = BackgroundScheduler()
            scheduler.add_job(move_log_to_archive, 'cron', hour=12, minute=00)
            scheduler.start()