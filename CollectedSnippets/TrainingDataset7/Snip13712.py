def _safe_init_worker(init_worker, counter, *args, **kwargs):
    try:
        init_worker(counter, *args, **kwargs)
    except Exception:
        with counter.get_lock():
            # Set a value that will not increment above zero any time soon.
            counter.value = -1000
        raise