def chunked_cursor(self):
        self._named_cursor_idx += 1
        # Get the current async task
        # Note that right now this is behind @async_unsafe, so this is
        # unreachable, but in future we'll start loosening this restriction.
        # For now, it's here so that every use of "threading" is
        # also async-compatible.
        try:
            current_task = asyncio.current_task()
        except RuntimeError:
            current_task = None
        # Current task can be none even if the current_task call didn't error
        if current_task:
            task_ident = str(id(current_task))
        else:
            task_ident = "sync"
        # Use that and the thread ident to get a unique name
        return self._cursor(
            name="_django_curs_%d_%s_%d"
            % (
                # Avoid reusing name in other threads / tasks
                threading.current_thread().ident,
                task_ident,
                self._named_cursor_idx,
            )
        )