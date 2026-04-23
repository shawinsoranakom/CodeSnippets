def wait(object_list, timeout=None):
        '''
        Wait till an object in object_list is ready/readable.

        Returns list of those objects in object_list which are ready/readable.
        '''
        with _WaitSelector() as selector:
            for obj in object_list:
                selector.register(obj, selectors.EVENT_READ)

            if timeout is not None:
                deadline = time.monotonic() + timeout

            while True:
                ready = selector.select(timeout)
                if ready:
                    return [key.fileobj for (key, events) in ready]
                else:
                    if timeout is not None:
                        timeout = deadline - time.monotonic()
                        if timeout < 0:
                            return ready