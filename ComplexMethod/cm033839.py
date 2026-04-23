def _run_loop(self, items: list[t.Any]) -> UnifiedTaskResult:
        """
        Runs the task with the loop items specified and collates the result
        into an array named 'results' which is inserted into the final result
        along with the item for which the loop ran.
        """
        task_ctx = TaskContext.current()

        task_ctx._loop_items = items

        self._task.loop_control.post_validate(templar=task_ctx.task_templar)
        self._check_loop_control()

        loop_pause = self._task.loop_control.pause

        ran_once = False
        last_loop_task: Task | None = None

        for _item_index, _item in task_ctx.start_loop():
            # pause between loop iterations
            if loop_pause and ran_once:
                time.sleep(loop_pause)
            else:
                ran_once = True

            with task_ctx.loop_item_context(self):
                last_loop_task = self._task

                utr = self._execute()

                if self._task.loop_control and self._task.loop_control.break_when:
                    try:
                        utr.set_break_when_result(self._task._resolve_conditional(self._task.loop_control.break_when, task_ctx.task_vars))
                    except AnsibleError as ex:
                        # RPFIX-5: UX: This this bypasses AnsibleTaskError handling, resulting in less information than a normal task failure.
                        utr.set_break_when_result(ex)

                self._update_task_connection()

                if utr.failed or utr.unreachable:
                    self._final_q.send_callback('v2_runner_item_on_failed', self._host, self._task, utr)
                elif utr.skipped:
                    self._final_q.send_callback('v2_runner_item_on_skipped', self._host, self._task, utr)
                else:
                    if self._task.diff:
                        # non-loop diff dispatch is handled controller-side by the strategy
                        self._final_q.send_callback('v2_on_file_diff', self._host, self._task, utr)

                    self._final_q.send_callback('v2_runner_item_on_ok', self._host, self._task, utr)

            # update the connection value on the original task to reflect the resolved value
            self._update_task_connection()

        if last_loop_task:
            # FUTURE: hide this in Task/LoopContext once they're fully implemented
            # NOTE: run_once cannot contain loop vars because it's templated earlier also
            # This is saving the post-validated field from the last loop so the strategy can use the templated value post task execution
            self._task.run_once = last_loop_task.run_once
            self._task.action = last_loop_task.action

        return task_ctx.build_loop_result()