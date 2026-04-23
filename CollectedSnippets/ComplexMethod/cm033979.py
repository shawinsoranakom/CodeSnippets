def v2_runner_on_ok(self, result: CallbackTaskResult) -> None:
        host_label = self.host_label(result)

        if isinstance(result.task, TaskInclude):
            if self._last_task_banner != result.task._uuid:
                self._print_task_banner(result.task)
            return
        elif result.result.get('changed', False):
            if self._last_task_banner != result.task._uuid:
                self._print_task_banner(result.task)

            msg = "changed: [%s]" % (host_label,)
            color = C.COLOR_CHANGED
        else:
            if not self.get_option('display_ok_hosts'):
                return

            if self._last_task_banner != result.task._uuid:
                self._print_task_banner(result.task)

            msg = "ok: [%s]" % (host_label,)
            color = C.COLOR_OK

        self._handle_warnings_and_exception(result)

        if result.task.loop and 'results' in result.result:
            self._process_items(result)
        else:
            self._clean_results(result.result, result.task.action)

            if self._run_is_verbose(result):
                msg += " => %s" % (self._dump_results(result.result),)
            self._display.display(msg, color=color)