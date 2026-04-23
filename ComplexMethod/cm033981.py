def v2_on_file_diff(self, result: CallbackTaskResult) -> None:
        if result.task.loop and 'results' in result.result:
            for res in result.result['results']:
                if 'diff' in res and res['diff'] and res.get('changed', False):
                    diff = self._get_diff(res['diff'])
                    if diff:
                        if self._last_task_banner != result.task._uuid:
                            self._print_task_banner(result.task)
                        self._display.display(diff)
        elif 'diff' in result.result and result.result['diff'] and result.result.get('changed', False):
            diff = self._get_diff(result.result['diff'])
            if diff:
                if self._last_task_banner != result.task._uuid:
                    self._print_task_banner(result.task)
                self._display.display(diff)