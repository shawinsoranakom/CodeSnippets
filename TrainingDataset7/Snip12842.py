def exhaust(stream_or_iterable):
    """Exhaust an iterator or stream."""
    try:
        iterator = iter(stream_or_iterable)
    except TypeError:
        iterator = ChunkIter(stream_or_iterable, 16384)
    collections.deque(iterator, maxlen=0)