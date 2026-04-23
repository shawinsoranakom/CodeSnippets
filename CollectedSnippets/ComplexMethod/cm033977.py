def _finish_task(self, status: str, result: IncludedFile | CallbackTaskResult) -> None:
        """ record the results of a task for a single host """

        if isinstance(result, CallbackTaskResult):
            task_uuid = result.task._uuid
            host_uuid = result.host._uuid
            host_name = result.host.name

            if self._fail_on_change == 'true' and status == 'ok' and result.result.get('changed', False):
                status = 'failed'
        else:
            task_uuid = result._task._uuid
            host_uuid = 'include'
            host_name = 'include'

        task_data = self._task_data[task_uuid]

        # ignore failure if expected and toggle result if asked for
        if status == 'failed' and 'EXPECTED FAILURE' in task_data.name:
            status = 'ok'
        elif 'TOGGLE RESULT' in task_data.name:
            if status == 'failed':
                status = 'ok'
            elif status == 'ok':
                status = 'failed'

        if task_data.name.startswith(self._test_case_prefix) or status == 'failed':
            task_data.add_host(HostData(host_uuid, host_name, status, result))