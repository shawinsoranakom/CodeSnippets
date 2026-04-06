def slow_sync_stream():
    yield {"n": 1}
    time.sleep(0.3)
    yield {"n": 2}