def put(self, obj, block=True, timeout=None, *,
            unbounditems=None,
            _delay=10 / 1000,  # 10 milliseconds
            ):
        """Add the object to the queue.

        If "block" is true, this blocks while the queue is full.

        For most objects, the object received through Queue.get() will
        be a new one, equivalent to the original and not sharing any
        actual underlying data.  The notable exceptions include
        cross-interpreter types (like Queue) and memoryview, where the
        underlying data is actually shared.  Furthermore, some types
        can be sent through a queue more efficiently than others.  This
        group includes various immutable types like int, str, bytes, and
        tuple (if the items are likewise efficiently shareable).  See interpreters.is_shareable().

        "unbounditems" controls the behavior of Queue.get() for the given
        object if the current interpreter (calling put()) is later
        destroyed.

        If "unbounditems" is None (the default) then it uses the
        queue's default, set with create_queue(),
        which is usually UNBOUND.

        If "unbounditems" is UNBOUND_ERROR then get() will raise an
        ItemInterpreterDestroyed exception if the original interpreter
        has been destroyed.  This does not otherwise affect the queue;
        the next call to put() will work like normal, returning the next
        item in the queue.

        If "unbounditems" is UNBOUND_REMOVE then the item will be removed
        from the queue as soon as the original interpreter is destroyed.
        Be aware that this will introduce an imbalance between put()
        and get() calls.

        If "unbounditems" is UNBOUND then it is returned by get() in place
        of the unbound item.
        """
        if not block:
            return self.put_nowait(obj, unbounditems=unbounditems)
        if unbounditems is None:
            unboundop = -1
        else:
            unboundop, = _serialize_unbound(unbounditems)
        if timeout is not None:
            timeout = int(timeout)
            if timeout < 0:
                raise ValueError(f'timeout value must be non-negative')
            end = time.time() + timeout
        while True:
            try:
                _queues.put(self._id, obj, unboundop)
            except QueueFull:
                if timeout is not None and time.time() >= end:
                    raise  # re-raise
                time.sleep(_delay)
            else:
                break