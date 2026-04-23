def _task_get_stack(task, limit):
    frames = []
    if hasattr(task._coro, 'cr_frame'):
        # case 1: 'async def' coroutines
        f = task._coro.cr_frame
    elif hasattr(task._coro, 'gi_frame'):
        # case 2: legacy coroutines
        f = task._coro.gi_frame
    elif hasattr(task._coro, 'ag_frame'):
        # case 3: async generators
        f = task._coro.ag_frame
    else:
        # case 4: unknown objects
        f = None
    if f is not None:
        while f is not None:
            if limit is not None:
                if limit <= 0:
                    break
                limit -= 1
            frames.append(f)
            f = f.f_back
        frames.reverse()
    elif task._exception is not None:
        tb = task._exception.__traceback__
        while tb is not None:
            if limit is not None:
                if limit <= 0:
                    break
                limit -= 1
            frames.append(tb.tb_frame)
            tb = tb.tb_next
    return frames