async def tee_peer(
    iterator: AsyncIterator[T],
    # the buffer specific to this peer
    buffer: deque[T],
    # the buffers of all peers, including our own
    peers: list[deque[T]],
    lock: AbstractAsyncContextManager[Any],
) -> AsyncGenerator[T, None]:
    """An individual iterator of a `tee`.

    This function is a generator that yields items from the shared iterator
    `iterator`. It buffers items until the least advanced iterator has yielded them as
    well.

    The buffer is shared with all other peers.

    Args:
        iterator: The shared iterator.
        buffer: The buffer for this peer.
        peers: The buffers of all peers.
        lock: The lock to synchronise access to the shared buffers.

    Yields:
        The next item from the shared iterator.
    """
    try:
        while True:
            if not buffer:
                async with lock:
                    # Another peer produced an item while we were waiting for the lock.
                    # Proceed with the next loop iteration to yield the item.
                    if buffer:
                        continue
                    try:
                        item = await anext(iterator)
                    except StopAsyncIteration:
                        break
                    else:
                        # Append to all buffers, including our own. We'll fetch our
                        # item from the buffer again, instead of yielding it directly.
                        # This ensures the proper item ordering if any of our peers
                        # are fetching items concurrently. They may have buffered their
                        # item already.
                        for peer_buffer in peers:
                            peer_buffer.append(item)
            yield buffer.popleft()
    finally:
        async with lock:
            # this peer is done - remove its buffer
            for idx, peer_buffer in enumerate(peers):  # pragma: no branch
                if peer_buffer is buffer:
                    peers.pop(idx)
                    break
            # if we are the last peer, try and close the iterator
            if not peers and hasattr(iterator, "aclose"):
                await iterator.aclose()