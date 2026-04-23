def _index(result):
    id2name, awaits, task_stacks = {}, [], {}
    for awaited_info in result:
        for task_info in awaited_info.awaited_by:
            task_id = task_info.task_id
            task_name = task_info.task_name
            id2name[task_id] = task_name

            # Store the internal coroutine stack for this task
            if task_info.coroutine_stack:
                for coro_info in task_info.coroutine_stack:
                    call_stack = coro_info.call_stack
                    internal_stack = [_format_stack_entry(frame) for frame in call_stack]
                    task_stacks[task_id] = internal_stack

            # Add the awaited_by relationships (external dependencies)
            if task_info.awaited_by:
                for coro_info in task_info.awaited_by:
                    call_stack = coro_info.call_stack
                    parent_task_id = coro_info.task_name
                    stack = [_format_stack_entry(frame) for frame in call_stack]
                    awaits.append((parent_task_id, stack, task_id))
    return id2name, awaits, task_stacks