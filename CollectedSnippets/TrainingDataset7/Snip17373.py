def sync_waiter(request):
    with sync_waiter.lock:
        sync_waiter.active_threads.add(threading.current_thread())
    sync_waiter.barrier.wait(timeout=0.5)
    return hello(request)