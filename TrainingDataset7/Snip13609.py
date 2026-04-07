async def aclosing_iterator_wrapper(iterable, close):
    try:
        async for chunk in iterable:
            yield chunk
    finally:
        request_finished.disconnect(close_old_connections)
        close()  # will fire request_finished
        request_finished.connect(close_old_connections)