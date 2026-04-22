def func_with_lock():
        if lock:
            with _config_lock:
                func()
        else:
            func()