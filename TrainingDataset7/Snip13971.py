def freeze_time(t):
    """
    Context manager to temporarily freeze time.time(). This temporarily
    modifies the time function of the time module. Modules which import the
    time function directly (e.g. `from time import time`) won't be affected
    This isn't meant as a public API, but helps reduce some repetitive code in
    Django's test suite.
    """
    _real_time = time.time
    time.time = lambda: t
    try:
        yield
    finally:
        time.time = _real_time