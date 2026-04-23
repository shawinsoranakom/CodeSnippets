def _execute_internal(self) -> UnifiedTaskResult:
        """
        The primary workhorse of the executor system, this runs the task
        on the specified host (which may be the delegated_to host) and handles
        the retry/until and block rescue/always execution
        """
        task_ctx = TaskContext.current()

        self._calculate_delegate_to()

        context_validation_error = None

        task_vars_with_magic_vars = task_ctx.task_vars.copy()  # copy of task vars with connection vars erased/augmented for delegate_to

        try:
            # TODO: remove play_context as this does not take delegation nor loops correctly into account,
            # the task itself should hold the correct values for connection/shell/become/terminal plugin options to finalize.
            #  Kept for now for backwards compatibility and a few functions that are still exclusive to it.

            # apply the given task's information to the connection info,
            # which may override some fields already set by the play or
            # the options specified on the command line
            self._play_context = self._play_context.set_task_and_variable_override(task=self._task, variables=task_ctx.task_vars, templar=task_ctx.task_templar)

            # fields set from the play/task may be based on task vars, so we have to
            # do the same kind of post validation step on it here before we use it.
            self._play_context.post_validate(templar=task_ctx.task_templar)

            # now that the play context is finalized, if the remote_addr is not set
            # default to using the host's address field as the remote address
            if not self._play_context.remote_addr:
                self._play_context.remote_addr = self._host.address

            # We also add "magic" variables back into the tempvars dict to make sure
            self._play_context.update_vars(task_vars_with_magic_vars)

        except AnsibleError as e:
            # save the error, which we'll raise later if we don't end up
            # skipping this task during the conditional evaluation step
            context_validation_error = e

        # Evaluate the conditional (if any) for this task, which we do before running
        # the final task post-validation. We do this before the post validation due to
        # the fact that the conditional may specify that the task be skipped due to a
        # variable not being present which would otherwise cause validation to fail
        try:
            conditional_result, conditional_item = self._task._resolve_conditional_with_item(self._task.when, task_vars_with_magic_vars)

            if not conditional_result:
                return UnifiedTaskResult.record_conditional_false(conditional_item)
        except AnsibleError as e:
            # FUTURE: this error handling seems problematic; shouldn't a failed loop expression always be an error, rather than letting an item-oriented `when`
            #  expression be treated as a task-oriented one and sweeping the failure under the rug if it happens to be False? If so, this re-raise and the
            #  one just below it should be removed in favor of letting it fly from get_loop_items.
            try:
                # The original error's obj should contain the failed expression, which should be origin tagged.
                # This error is intended to provide additional context (the message) for the original error.
                # By repeating the original error's obj here, the error display will group the two errors together.
                raise AnsibleError("A 'when' expression failed.", obj=e.obj) from e
            except AnsibleError as ae:
                if self._loop_eval_error is None:
                    raise

                # Display the error from the conditional as well to prevent
                # losing information useful for debugging.
                display.error(ae)

            raise self._loop_eval_error

        # Not skipping, if we had loop error raised earlier we need to raise it now to halt the execution of this task
        if self._loop_eval_error is not None:
            raise self._loop_eval_error

        # if we ran into an error while setting up the PlayContext, raise it now, unless is known issue with delegation
        # and undefined vars (correct values are in cvars later on and connection plugins, if still error, blows up there)

        # DTFIX-FUTURE: this should probably be declaratively handled in post_validate (or better, get rid of play_context)
        if context_validation_error is not None:
            raiseit = True
            if self._task.delegate_to:
                if isinstance(context_validation_error, AnsibleParserError):
                    # parser error, might be cause by undef too
                    if isinstance(context_validation_error.__cause__, AnsibleUndefinedVariable):
                        raiseit = False
                elif isinstance(context_validation_error, AnsibleUndefinedVariable):
                    # DTFIX-FUTURE: should not be possible to hit this now (all are AnsibleFieldAttributeError)?
                    raiseit = False
            if raiseit:
                raise context_validation_error  # pylint: disable=raising-bad-type

        # Now we do final validation on the task, which sets all fields to their final values.
        self._task.post_validate(templar=task_ctx.task_templar.extend(variables=task_vars_with_magic_vars))  # should be handled by a context!

        # if this task is a TaskInclude, we just return now with a success code so the
        # main thread can expand the task list for the given host
        if self._task.action in C._ACTION_INCLUDE_TASKS:
            include_args = self._task.args.copy()
            include_file = include_args.pop('_raw_params', None)

            with UnifiedTaskResult.create_and_record() as utr:
                utr.include_file = include_file
                utr.include_args = include_args
                return utr

        # if this task is a IncludeRole, we just return now with a success code so the main thread can expand the task list for the given host
        elif self._task.action in C._ACTION_INCLUDE_ROLE:
            include_args = self._task.args.copy()

            with UnifiedTaskResult.create_and_record() as utr:
                utr.include_args = include_args
                return utr

        # setup cvars copy, used for all connection related templating
        if self._task.delegate_to:
            # use vars from delegated host (which already include task vars) instead of original host
            cvars = task_ctx.task_vars.get('ansible_delegated_vars', {}).get(self._task.delegate_to, {})
        else:
            # just use normal host vars
            cvars = task_ctx.task_vars

        connection_templar = task_ctx.task_templar.extend(variables=cvars)  # should be managed by a context!

        # use magic var if it exists, if not, let task inheritance do it's thing.
        if cvars.get('ansible_connection') is not None:
            current_connection = connection_templar.template(cvars['ansible_connection'])
        else:
            current_connection = self._task.connection

        # get the connection and the handler for this execution
        if (not self._connection or
                not getattr(self._connection, 'connected', False) or
                not self._connection.matches_name([current_connection]) or
                # pc compare, left here for old plugins, but should be irrelevant for those
                # using get_option, since they are cleared each iteration.
                self._play_context.remote_addr != self._connection._play_context.remote_addr):
            self._connection = self._get_connection(cvars, connection_templar, current_connection)
        else:
            # if connection is reused, its _play_context is no longer valid and needs
            # to be replaced with the one templated above, in case other data changed
            self._connection._play_context = self._play_context
            self._set_become_plugin(cvars, connection_templar, self._connection)

        plugin_vars = self._set_connection_options(cvars, connection_templar)

        # update with connection info (i.e ansible_host/ansible_user)
        self._connection.update_vars(task_ctx.task_vars)

        # TODO: eventually remove as pc is taken out of the resolution path
        # feed back into pc to ensure plugins not using get_option can get correct value
        self._connection._play_context = self._play_context.set_task_and_variable_override(
            task=self._task,
            variables=task_ctx.task_vars,
            templar=task_ctx.task_templar,
        )

        # TODO: eventually remove this block as this should be a 'consequence' of 'forced_local' modules, right now rely on remote_is_local connection
        # special handling for python interpreter for network_os, default to ansible python unless overridden
        if 'ansible_python_interpreter' not in cvars and 'ansible_network_os' in cvars and getattr(self._connection, '_remote_is_local', False):
            # this also avoids 'python discovery'
            cvars['ansible_python_interpreter'] = sys.executable

        # get handler
        self._handler, _module_context = self._get_action_handler_with_module_context(templar=task_ctx.task_templar)

        # self._connection should have its final value for this task/loop-item by this point; record on the task object
        self._update_task_connection()

        retries = 1  # includes the default actual run + retries set by user/default
        if self._task.retries is not None:
            retries += max(0, self._task.retries)
        elif self._task.until:
            retries += 3  # the default is not set in FA because we need to differentiate "unset" value

        delay = self._task.delay
        if delay < 0:
            delay = 1

        display.debug("starting attempt loop")
        for attempt in range(1, retries + 1):
            display.debug("running the handler")
            try:
                # FUTURE: exceptions raised anywhere here bypass failed_when, `until` retries, intra-loop register/register-projections
                with _task_timeout.TaskTimeoutError.alarm_timeout(self._task.timeout):
                    try:
                        task_ctx.pending_changes = _task.PendingChanges()

                        with UnifiedTaskResult.create_and_record(self._handler.run(task_vars=task_ctx.task_vars)) as utr:
                            utr.pending_changes = task_ctx.pending_changes
                    finally:
                        task_ctx.pending_changes = None

            finally:
                self._handler.cleanup()
            display.debug("handler run complete")

            if self._task.async_val > 0:
                if self._task.poll > 0 and not utr.skipped and not utr.failed:
                    utr = self._poll_async_result(utr=utr, templar=task_ctx.task_templar, task_vars=task_ctx.task_vars)

                    if utr.failed:
                        self._final_q.send_callback('v2_runner_on_async_failed', self._host, self._task, utr)
                    else:
                        self._final_q.send_callback('v2_runner_on_async_ok', self._host, self._task, utr)

            if utr.ansible_facts and _task.VariableLayer.CACHEABLE_FACT not in utr.pending_changes.register_host_variables:
                # For backward compatibility, if the action provided ansible_facts, use that as the CACHEABLE_FACT layer if the action did not provide one.
                utr.pending_changes.register_host_variables[_task.VariableLayer.CACHEABLE_FACT] = utr.ansible_facts

            # Variable layers should be reflected on task vars in the same way they will be handled by variable manager.
            # What occurs below is a partial re-implementation of variable manager, and thus does not fully reflect its behavior.
            # These updates are only done for the current host.

            if not self._task.delegate_to or not self._task.delegate_facts:
                if cacheable_fact_layer := utr.pending_changes.register_host_variables.get(_task.VariableLayer.CACHEABLE_FACT):
                    task_ctx.update_task_vars(dict(
                        ansible_facts=combine_vars(
                            task_ctx.task_vars.get('ansible_facts', {}),
                            namespace_facts(cacheable_fact_layer)['ansible_facts'],
                        ),
                    ))

                    if _INJECT_FACTS:
                        task_ctx.update_task_vars(_clean_and_deprecate_top_level_facts(cacheable_fact_layer))

                if include_vars_layer := utr.pending_changes.register_host_variables.get(_task.VariableLayer.INCLUDE_VARS):
                    task_ctx.update_task_vars(include_vars_layer)

                if ephemeral_fact_layer := utr.pending_changes.register_host_variables.get(_task.VariableLayer.EPHEMERAL_FACT):
                    task_ctx.update_task_vars(ephemeral_fact_layer)

            if register_vars_layer := utr.pending_changes.register_host_variables.get(_task.VariableLayer.REGISTER_VARS):
                task_ctx.update_task_vars(register_vars_layer)

            # Make attempts and retries available early to allow their use in changed/failed_when
            if retries > 1:
                utr.attempts = attempt

            # if we didn't skip this task, use the helpers to evaluate the changed/
            # failed_when properties
            if not utr.skipped:
                try:
                    if self._task.changed_when:
                        utr.set_changed_when_result(self._task._resolve_conditional(self._task.changed_when, task_ctx.task_vars))
                except AnsibleError as e:
                    utr.set_changed_when_result(e)
                else:
                    try:
                        if self._task.failed_when:
                            utr.set_failed_when_result(self._task._resolve_conditional(self._task.failed_when, task_ctx.task_vars))
                    except AnsibleError as e:
                        utr.set_failed_when_result(e)

            if retries > 1:
                try:
                    if self._task._resolve_conditional(self._task.until or [not utr.failed], task_ctx.task_vars):
                        break
                except AnsibleError as e:
                    # The original error's obj should contain the failed expression, which should be origin tagged.
                    # This error is intended to provide additional context (the message) for the original error.
                    # By repeating the original error's obj here, the error display will group the two errors together.
                    raise AnsibleError("An 'until' expression failed.", obj=e.obj) from e

                # no conditional check, or it failed, so sleep for the specified time
                if attempt < retries:
                    utr.retries = retries
                    utr.attempts = attempt + 1
                    display.debug('Retrying task, attempt %d of %d' % (attempt, retries))
                    self._final_q.send_callback('v2_runner_retry', self._host, self._task, utr)
                    time.sleep(delay)
                    self._handler = self._get_action_handler(templar=task_ctx.task_templar)
        else:
            if retries > 1:
                # we ran out of attempts, so mark the result as failed
                utr.attempts = retries - 1
                utr.failed = True

        # save the notification target in the result, if it was specified, as
        # this task may be running in a loop in which case the notification
        # may be item-specific, ie. "notify: service {{item}}"
        if self._task.notify is not None:
            utr.notify = self._task.notify

        # add the delegated vars to the result, so we can reference them
        # on the results side without having to do any further templating
        # also now add connection vars results when delegating
        if self._task.delegate_to:
            utr.delegated_host = self._task.delegate_to
            utr.callback_delegated_vars_subset = dict(
                ansible_delegated_host=self._task.delegate_to,
                ansible_connection=current_connection,
            )

            # note: here for callbacks that rely on this info to display delegation
            for plugin_var_name in plugin_vars:
                if plugin_var_name not in _DELEGATED_CONNECTION_PLUGIN_VAR_NAMES:
                    continue

                # FUTURE: this is horribly inefficient
                for plugin_option_name in C.config.get_plugin_options_from_var("connection", current_connection, plugin_var_name):
                    utr.callback_delegated_vars_subset[plugin_var_name] = self._connection.get_option(plugin_option_name)

        # and return
        display.debug("attempt loop complete, returning result")
        return utr