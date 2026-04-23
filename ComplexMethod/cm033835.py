def _insert_tasks_into_state(self, state, task_list):
        # if we've failed at all, or if the task list is empty, just return the current state
        if (state.fail_state != FailedStates.NONE and state.run_state == IteratingStates.TASKS) or not task_list:
            return state

        if state.run_state == IteratingStates.TASKS:
            if state.tasks_child_state:
                state.tasks_child_state = self._insert_tasks_into_state(state.tasks_child_state, task_list)
            else:
                target_block = state._blocks[state.cur_block].copy(exclude_tasks=True)
                target_block.block[state.cur_regular_task:state.cur_regular_task] = task_list
                state._blocks[state.cur_block] = target_block
        elif state.run_state == IteratingStates.RESCUE:
            if state.rescue_child_state:
                state.rescue_child_state = self._insert_tasks_into_state(state.rescue_child_state, task_list)
            else:
                target_block = state._blocks[state.cur_block].copy(exclude_tasks=True)
                target_block.rescue[state.cur_rescue_task:state.cur_rescue_task] = task_list
                state._blocks[state.cur_block] = target_block
        elif state.run_state == IteratingStates.ALWAYS:
            if state.always_child_state:
                state.always_child_state = self._insert_tasks_into_state(state.always_child_state, task_list)
            else:
                target_block = state._blocks[state.cur_block].copy(exclude_tasks=True)
                target_block.always[state.cur_always_task:state.cur_always_task] = task_list
                state._blocks[state.cur_block] = target_block
        elif state.run_state == IteratingStates.HANDLERS:
            state.handlers[state.cur_handlers_task:state.cur_handlers_task] = [h for b in task_list for h in b.block]

        return state