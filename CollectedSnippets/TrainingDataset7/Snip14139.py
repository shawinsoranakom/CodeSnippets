def decorator(func):
        @wraps(func)
        def inner(*args, **kwargs):
            # Detect a running event loop in this thread.
            try:
                get_running_loop()
            except RuntimeError:
                pass
            else:
                if not os.environ.get("DJANGO_ALLOW_ASYNC_UNSAFE"):
                    raise SynchronousOnlyOperation(message)
            # Pass onward.
            return func(*args, **kwargs)

        return inner