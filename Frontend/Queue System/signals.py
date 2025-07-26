import threading

# Event برای بیدار کردن Scheduler
wake_event = threading.Event()

def wake_scheduler():
    wake_event.set()
