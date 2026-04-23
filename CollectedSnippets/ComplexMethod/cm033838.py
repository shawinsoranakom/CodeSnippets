def run(self) -> UnifiedTaskResult:
        """
        The main executor entrypoint, where we determine if the specified
        task requires looping and either runs the task with self._run_loop()
        or self._execute(). After that, the returned results are parsed and
        returned as a dict.
        """

        display.debug("in run() - task %s" % self._task._uuid)

        task_ctx = TaskContext.current()

        try:
            try:
                items = self._get_loop_items()
            except AnsibleUndefinedVariable as e:
                # save the error raised here for use later
                items = None
                self._loop_eval_error = e

            if items is None:  # non-loop
                utr = self._execute()
            elif not items:  # empty loop
                with UnifiedTaskResult.create_and_record() as utr:
                    utr.set_skipped('No items in the list', include_skipped_reason=True)
                    utr.loop_results = []
            else:  # loop with values
                utr = self._run_loop(items)

            return utr
        except Exception as ex:
            utr = UnifiedTaskResult.create_from_action_exception(ex)

            self._task.update_result_no_log(task_ctx.task_templar, utr)

            if not isinstance(ex, AnsibleError):
                utr.msg = f'Unexpected failure during task execution: {utr.msg}'

            return utr
        finally:
            try:
                self._connection.close()
            except AttributeError:
                pass
            except Exception as e:
                display.debug(u"error closing connection: %s" % to_text(e))