def _build_linear_stacks(self, leaf_task_ids, task_map, child_to_parent):
        for leaf_id in leaf_task_ids:
            frames = []
            visited = set()
            current_id = leaf_id
            thread_id = None

            # Follow the single parent chain from leaf to root
            while current_id is not None:
                # Cycle detection
                if current_id in visited:
                    break
                visited.add(current_id)

                # Check if task exists in task_map
                if current_id not in task_map:
                    break

                task_info, tid = task_map[current_id]

                # Set thread_id from first task
                if thread_id is None:
                    thread_id = tid

                # Add all frames from all coroutines in this task
                if task_info.coroutine_stack:
                    for coro_info in task_info.coroutine_stack:
                        for frame in coro_info.call_stack:
                            frames.append(frame)

                # Get pre-computed parent info (no sorting needed!)
                parent_info = child_to_parent.get(current_id)

                # Add task boundary marker with parent count annotation if multiple parents
                task_name = task_info.task_name or "Task-" + str(task_info.task_id)
                if parent_info:
                    selected_parent, parent_count = parent_info
                    if parent_count > 1:
                        task_name = f"{task_name} ({parent_count} parents)"
                    frames.append(FrameInfo(("<task>", None, task_name, None)))
                    current_id = selected_parent
                else:
                    # Root task - no parent
                    frames.append(FrameInfo(("<task>", None, task_name, None)))
                    current_id = None

            # Yield the complete stack if we collected any frames
            if frames and thread_id is not None:
                yield frames, thread_id, leaf_id