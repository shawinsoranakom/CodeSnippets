def closing_iterator_wrapper(iterable, close):
    try:
        yield from iterable
    finally:
        request_finished.disconnect(close_old_connections)
        close()  # will fire request_finished
        request_finished.connect(close_old_connections)