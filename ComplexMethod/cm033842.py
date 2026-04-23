def _poll_async_result(self, utr: UnifiedTaskResult, templar: TemplateEngine, task_vars: dict[str, t.Any]) -> UnifiedTaskResult:
        """
        Polls for the specified JID to be complete
        """
        async_jid = utr.async_job_id

        if async_jid is None:
            # RPFIX-9: FUTURE: why not raise?
            with UnifiedTaskResult.create_and_record() as utr:
                utr.failed = True
                utr.msg = "No job id was returned by the async task"

            return utr

        # Create a new pseudo-task to run the async_status module, and run
        # that (with a sleep for "poll" seconds between each retry) until the
        # async time limit is exceeded.

        async_task = Task.load(dict(
            action='async_status',
            args={'jid': async_jid},
            check_mode=self._task.check_mode,
            environment=self._task.environment,
            delegate_to=self._task.delegate_to,
        ))

        # ensure that the synthetic async task has the resolved connection recorded on it
        self._update_task_connection(async_task)

        # FIXME: this is no longer the case, normal takes care of all, see if this can just be generalized
        # Because this is an async task, the action handler is async. However,
        # we need the 'normal' action handler for the status check, so get it
        # now via the action_loader
        async_handler: ActionBase = self._shared_loader_obj.action_loader.get(
            'ansible.legacy.async_status',
            task=async_task,
            connection=self._connection,
            play_context=self._play_context,
            loader=self._loader,
            templar=Templar._from_template_engine(templar),
            shared_loader_obj=self._shared_loader_obj,
        )

        time_left = self._task.async_val
        while time_left > 0:
            time.sleep(self._task.poll)

            try:
                with UnifiedTaskResult.create_and_record(async_handler.run(task_vars=task_vars)) as async_utr:
                    pass
                # We do not bail out of the loop in cases where the failure
                # is associated with a parsing error. The async_runner can
                # have issues which result in a half-written/unparsable result
                # file on disk, which manifests to the user as a timeout happening
                # before it's time to timeout.
                if async_utr.finished or (async_utr.failed and async_utr.ansible_parsed) or async_utr.skipped:
                    break
            except Exception as e:
                # Connections can raise exceptions during polling (eg, network bounce, reboot); these should be non-fatal.
                # On an exception, call the connection's reset method if it has one
                # (eg, drop/recreate WinRM connection; some reused connections are in a broken state)
                display.vvvv("Exception during async poll, retrying... (%s)" % to_text(e))
                display.debug("Async poll exception was:\n%s" % to_text(traceback.format_exc()))
                try:
                    async_handler._connection.reset()
                except AttributeError:
                    pass

                # Little hack to raise the exception if we've exhausted the timeout period
                time_left -= self._task.poll
                if time_left <= 0:
                    raise
            else:
                time_left -= self._task.poll
                self._final_q.send_callback('v2_runner_on_async_poll', self._host, async_task, async_utr)

        if not async_utr.finished:
            # RPFIX-9: FUTURE: why not raise?
            with UnifiedTaskResult.create_and_record() as async_failed_utr:
                async_failed_utr.failed = True
                async_failed_utr.async_result = async_utr.as_result_dict()

                if async_failed_utr.ansible_parsed:
                    async_failed_utr.msg = "async task did not complete within the requested time - %ss" % self._task.async_val
                else:
                    async_failed_utr.msg = "async task produced unparsable results"

            async_utr = async_failed_utr  # replace the actual async result with a synthesized failure
        else:
            # If the async task finished, automatically cleanup the temporary
            # status file left behind.
            cleanup_task = Task.load(
                {
                    'async_status': {
                        'jid': async_jid,
                        'mode': 'cleanup',
                    },
                    'check_mode': self._task.check_mode,
                    'environment': self._task.environment,
                    'delegate_to': self._task.delegate_to,
                }
            )
            cleanup_handler: ActionBase = self._shared_loader_obj.action_loader.get(
                'ansible.legacy.async_status',
                task=cleanup_task,
                connection=self._connection,
                play_context=self._play_context,
                loader=self._loader,
                templar=Templar._from_template_engine(templar),
                shared_loader_obj=self._shared_loader_obj,
            )
            cleanup_handler.run(task_vars=task_vars)
            cleanup_handler.cleanup(force=True)
            async_handler.cleanup(force=True)

        return async_utr