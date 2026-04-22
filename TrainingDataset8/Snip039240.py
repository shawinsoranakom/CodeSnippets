def test_repr_thread_class():
    import threading

    thread = threading.current_thread()
    # This should return a non empty string and not raise an exception.
    assert str(thread) is not None