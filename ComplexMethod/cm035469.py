def _wait_until_alive_impl(self) -> None:
        self.log('debug', f'Waiting for runtime to be alive at url: {self.runtime_url}')
        self.log(
            'debug',
            f'Sending request to: {self.config.sandbox.remote_runtime_api_url}/runtime/{self.runtime_id}',
        )
        runtime_info_response = self._send_runtime_api_request(
            'GET',
            f'{self.config.sandbox.remote_runtime_api_url}/runtime/{self.runtime_id}',
        )
        runtime_data = runtime_info_response.json()
        self.log(
            'debug',
            f'received response: {runtime_data}',
        )
        assert 'runtime_id' in runtime_data
        assert runtime_data['runtime_id'] == self.runtime_id
        assert 'pod_status' in runtime_data
        pod_status = runtime_data['pod_status'].lower()
        self.log('debug', f'Pod status: {pod_status}')
        restart_count = runtime_data.get('restart_count', 0)
        if restart_count != 0:
            restart_reasons = runtime_data.get('restart_reasons')
            self.log(
                'debug', f'Pod restarts: {restart_count}, reasons: {restart_reasons}'
            )

        # FIXME: We should fix it at the backend of /start endpoint, make sure
        # the pod is created before returning the response.
        # Retry a period of time to give the cluster time to start the pod
        if pod_status == 'ready':
            try:
                self.check_if_alive()
            except httpx.HTTPError as e:
                self.log(
                    'warning',
                    f"Runtime /alive failed, but pod says it's ready: {str(e)}",
                )
                raise AgentRuntimeNotReadyError(
                    f'Runtime /alive failed to respond with 200: {str(e)}'
                )
            return
        elif (
            pod_status == 'not found'
            or pod_status == 'pending'
            or pod_status == 'running'
        ):  # nb: Running is not yet Ready
            raise AgentRuntimeNotReadyError(
                f'Runtime (ID={self.runtime_id}) is not yet ready. Status: {pod_status}'
            )
        elif pod_status in ('failed', 'unknown', 'crashloopbackoff'):
            if pod_status == 'crashloopbackoff':
                raise AgentRuntimeUnavailableError(
                    'Runtime crashed and is being restarted, potentially due to memory usage. Please try again.'
                )
            else:
                raise AgentRuntimeUnavailableError(
                    f'Runtime is unavailable (status: {pod_status}). Please try again.'
                )
        else:
            # Maybe this should be a hard failure, but passing through in case the API changes
            self.log('warning', f'Unknown pod status: {pod_status}')

        self.log(
            'debug',
            f'Waiting for runtime pod to be active. Current status: {pod_status}',
        )
        raise AgentRuntimeNotReadyError()