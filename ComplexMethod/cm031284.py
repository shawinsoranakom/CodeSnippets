def build_task_table(result):
    id2name, _, _ = _index(result)
    table = []

    for awaited_info in result:
        thread_id = awaited_info.thread_id
        for task_info in awaited_info.awaited_by:
            # Get task info
            task_id = task_info.task_id
            task_name = task_info.task_name

            # Build coroutine stack string
            frames = [frame for coro in task_info.coroutine_stack
                     for frame in coro.call_stack]
            coro_stack = " -> ".join(_format_stack_entry(x).split(" ")[0]
                                   for x in frames)

            # Handle tasks with no awaiters
            if not task_info.awaited_by:
                table.append([thread_id, hex(task_id), task_name, coro_stack,
                            "", "", "0x0"])
                continue

            # Handle tasks with awaiters
            for coro_info in task_info.awaited_by:
                parent_id = coro_info.task_name
                awaiter_frames = [_format_stack_entry(x).split(" ")[0]
                                for x in coro_info.call_stack]
                awaiter_chain = " -> ".join(awaiter_frames)
                awaiter_name = id2name.get(parent_id, "Unknown")
                parent_id_str = (hex(parent_id) if isinstance(parent_id, int)
                               else str(parent_id))

                table.append([thread_id, hex(task_id), task_name, coro_stack,
                            awaiter_chain, awaiter_name, parent_id_str])

    return table