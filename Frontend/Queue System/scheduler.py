import logging
import os
import time
from django.conf import settings
from .models import UploadQueue
from .upload_manager import process_upload, executor
from .signals import wake_event 

# تنظیم مسیر لاگ Scheduler
SCHEDULER_LOG_FILE = os.path.join(settings.BASE_DIR, "logs", "scheduler.log")
os.makedirs(os.path.dirname(SCHEDULER_LOG_FILE), exist_ok=True)

scheduler_logger = logging.getLogger("scheduler_logger")
scheduler_logger.setLevel(logging.INFO)
if not scheduler_logger.handlers:
    fh = logging.FileHandler(SCHEDULER_LOG_FILE)
    fh.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(message)s"))
    scheduler_logger.addHandler(fh)

# def scheduler_loop():
#     scheduler_logger.info("Scheduler started and waiting for tasks...")
#     while True:
#         wake_event.wait()  # منتظر بیداری
#         wake_event.clear()
#         scheduler_logger.info("Scheduler woke up. Checking upload queue...")

#         while True:
#             tasks = UploadQueue.objects.filter(status__in=['failed', 'pending'])
#             if not tasks.exists():
#                 scheduler_logger.info("No more tasks in queue. Scheduler going to sleep.")
#                 break

#             scheduler_logger.info(f"Found {tasks.count()} tasks. Retrying uploads...")
#             for task in tasks:
#                 scheduler_logger.info(f"-> Retrying upload: {task.remote_filename}")
#                 executor.submit(process_upload, task.local_path, task.remote_dir, task.remote_filename, task)

#             time.sleep(5)  # تاخیر کوتاه برای کنترل فشار
def scheduler_loop():
    scheduler_logger.info("Scheduler started and waiting for tasks...")

    # هنگام استارت، اگر صف داریم → بیداری فوری
    from .models import UploadQueue
    if UploadQueue.objects.filter(status__in=['failed', 'pending']).exists():
        scheduler_logger.info("Found pending/failed tasks at startup. Processing now...")
        wake_event.set()

    while True:
        wake_event.wait()  # منتظر بیداری
        wake_event.clear()
        scheduler_logger.info("Scheduler woke up. Checking upload queue...")

        while True:
            tasks = UploadQueue.objects.filter(status__in=['failed', 'pending'])
            if not tasks.exists():
                scheduler_logger.info("No more tasks in queue. Scheduler going to sleep.")
                break

            scheduler_logger.info(f"Found {tasks.count()} tasks. Processing...")
            for task in tasks:
                if task.status == 'pending':
                    scheduler_logger.info(f"!!! Trying upload: {task.remote_filename}")
                    executor.submit(process_upload, task.local_path, task.remote_dir, task.remote_filename, task)
                if task.status == 'failed':
                    scheduler_logger.info(f"!!! Retrying failed upload: {task.remote_filename}")
                    executor.submit(process_upload, task.local_path, task.remote_dir, task.remote_filename, task)

            time.sleep(5)
