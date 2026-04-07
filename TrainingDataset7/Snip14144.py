def raise_last_exception():
    if _exception is not None:
        raise _exception[1]