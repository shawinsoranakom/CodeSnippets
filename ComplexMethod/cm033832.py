def _get_next_task_from_state(self, state, host):

        task = None

        # try and find the next task, given the current state.
        while True:
            # try to get the current block from the list of blocks, and
            # if we run past the end of the list we know we're done with
            # this block
            try:
                block = state._blocks[state.cur_block]
            except IndexError:
                state.run_state = IteratingStates.COMPLETE
                return (state, None)

            if state.run_state == IteratingStates.SETUP:
                # Gather facts if the default is 'smart' and we have not yet
                # done it for this host; or if 'explicit' and the play sets
                # gather_facts to True; or if 'implicit' and the play does
                # NOT explicitly set gather_facts to False.
                gather_facts = len(self._blocks[0].block) >= 1
                gathering = C.DEFAULT_GATHERING
                implied = self._play.gather_facts is None or boolean(self._play.gather_facts, strict=False)
                if gather_facts and (
                    (gathering == 'implicit' and implied) or
                    (gathering == 'explicit' and boolean(self._play.gather_facts, strict=False)) or
                    (gathering == 'smart' and implied and not self._variable_manager._facts_gathered_for_host(host.name))
                ):
                    task = self._blocks[0].block[0]

                state.run_state = IteratingStates.VALIDATE

            elif state.run_state == IteratingStates.VALIDATE:
                if len(self._blocks[0].block) >= 2 and self._play.validate_argspec:
                    task = self._blocks[0].block[1]

                state.run_state = IteratingStates.TASKS
                if not state.did_start_at_task:
                    state.cur_block += 1
                    state.cur_regular_task = 0
                    state.cur_rescue_task = 0
                    state.cur_always_task = 0
                    state.tasks_child_state = None
                    state.rescue_child_state = None
                    state.always_child_state = None

            elif state.run_state == IteratingStates.TASKS:
                # First, we check for a child task state that is not failed, and if we
                # have one recurse into it for the next task. If we're done with the child
                # state, we clear it and drop back to getting the next task from the list.
                if state.tasks_child_state:
                    (state.tasks_child_state, task) = self._get_next_task_from_state(state.tasks_child_state, host=host)
                    if self._check_failed_state(state.tasks_child_state):
                        # failed child state, so clear it and move into the rescue portion
                        state.tasks_child_state = None
                        self._set_failed_state(state)
                    else:
                        # get the next task recursively
                        if task is None or state.tasks_child_state.run_state == IteratingStates.COMPLETE:
                            # we're done with the child state, so clear it and continue
                            # back to the top of the loop to get the next task
                            state.tasks_child_state = None
                            continue
                else:
                    # First here, we check to see if we've failed anywhere down the chain
                    # of states we have, and if so we move onto the rescue portion. Otherwise,
                    # we check to see if we've moved past the end of the list of tasks. If so,
                    # we move into the always portion of the block, otherwise we get the next
                    # task from the list.
                    if self._check_failed_state(state):
                        state.run_state = IteratingStates.RESCUE
                    elif state.cur_regular_task >= len(block.block):
                        state.run_state = IteratingStates.ALWAYS
                    else:
                        task = block.block[state.cur_regular_task]
                        # if the current task is actually a child block, create a child
                        # state for us to recurse into on the next pass
                        if isinstance(task, Block):
                            state.tasks_child_state = HostState(blocks=[task])
                            state.tasks_child_state.run_state = IteratingStates.TASKS
                            # since we've created the child state, clear the task
                            # so we can pick up the child state on the next pass
                            task = None
                        state.cur_regular_task += 1

            elif state.run_state == IteratingStates.RESCUE:
                # The process here is identical to IteratingStates.TASKS, except instead
                # we move into the always portion of the block.
                if state.rescue_child_state:
                    (state.rescue_child_state, task) = self._get_next_task_from_state(state.rescue_child_state, host=host)
                    if self._check_failed_state(state.rescue_child_state):
                        state.rescue_child_state = None
                        self._set_failed_state(state)
                    else:
                        if task is None or state.rescue_child_state.run_state == IteratingStates.COMPLETE:
                            state.rescue_child_state = None
                            continue
                else:
                    if state.fail_state & FailedStates.RESCUE == FailedStates.RESCUE:
                        state.run_state = IteratingStates.ALWAYS
                    elif state.cur_rescue_task >= len(block.rescue):
                        if len(block.rescue) > 0:
                            state.fail_state = FailedStates.NONE
                        state.run_state = IteratingStates.ALWAYS
                        state.did_rescue = True
                    else:
                        task = block.rescue[state.cur_rescue_task]
                        if isinstance(task, Block):
                            state.rescue_child_state = HostState(blocks=[task])
                            state.rescue_child_state.run_state = IteratingStates.TASKS
                            task = None
                        state.cur_rescue_task += 1

            elif state.run_state == IteratingStates.ALWAYS:
                # And again, the process here is identical to IteratingStates.TASKS, except
                # instead we either move onto the next block in the list, or we set the
                # run state to IteratingStates.COMPLETE in the event of any errors, or when we
                # have hit the end of the list of blocks.
                if state.always_child_state:
                    (state.always_child_state, task) = self._get_next_task_from_state(state.always_child_state, host=host)
                    if self._check_failed_state(state.always_child_state):
                        state.always_child_state = None
                        self._set_failed_state(state)
                    else:
                        if task is None or state.always_child_state.run_state == IteratingStates.COMPLETE:
                            state.always_child_state = None
                            continue
                else:
                    if state.cur_always_task >= len(block.always):
                        if state.fail_state != FailedStates.NONE:
                            state.run_state = IteratingStates.COMPLETE
                        else:
                            state.cur_block += 1
                            state.cur_regular_task = 0
                            state.cur_rescue_task = 0
                            state.cur_always_task = 0
                            state.run_state = IteratingStates.TASKS
                            state.tasks_child_state = None
                            state.rescue_child_state = None
                            state.always_child_state = None
                            state.did_rescue = False
                    else:
                        task = block.always[state.cur_always_task]
                        if isinstance(task, Block):
                            state.always_child_state = HostState(blocks=[task])
                            state.always_child_state.run_state = IteratingStates.TASKS
                            task = None
                        state.cur_always_task += 1

            elif state.run_state == IteratingStates.HANDLERS:
                if state.update_handlers:
                    # reset handlers for HostState since handlers from include_tasks
                    # might be there from previous flush
                    state.handlers = self.handlers[:]
                    state.update_handlers = False

                while True:
                    try:
                        task = state.handlers[state.cur_handlers_task]
                    except IndexError:
                        task = None
                        state.cur_handlers_task = 0
                        state.run_state = state.pre_flushing_run_state
                        state.update_handlers = True
                        break
                    else:
                        state.cur_handlers_task += 1
                        if task.is_host_notified(host):
                            return state, task

            elif state.run_state == IteratingStates.COMPLETE:
                return (state, None)

            # if something above set the task, break out of the loop now
            if task:
                # skip implicit flush_handlers if there are no handlers notified
                if (
                    task.implicit
                    and task._get_meta() == 'flush_handlers'
                    and (
                        # the state store in the `state` variable could be a nested state,
                        # notifications are always stored in the top level state, get it here
                        not self.get_state_for_host(host.name).handler_notifications
                        # in case handlers notifying other handlers, the notifications are not
                        # saved in `handler_notifications` and handlers are notified directly
                        # to prevent duplicate handler runs, so check whether any handler
                        # is notified
                        and all(not h.notified_hosts for h in self.handlers)
                    )
                ):
                    display.debug("No handler notifications for %s, skipping." % host.name)
                elif (
                    (role := task._role)
                    and role._metadata.allow_duplicates is False
                    and host.name in self._play._get_cached_role(role)._completed
                ):
                    display.debug("'%s' skipped because role has already run" % task)
                else:
                    break

        return (state, task)