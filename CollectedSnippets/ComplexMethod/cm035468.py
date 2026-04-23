def _check_existing_runtime(self) -> bool:
        self.log('info', f'Checking for existing runtime with session ID: {self.sid}')
        try:
            response = self._send_runtime_api_request(
                'GET',
                f'{self.config.sandbox.remote_runtime_api_url}/sessions/{self.sid}',
            )
            data = response.json()
            status = data.get('status')
            self.log('info', f'Found runtime with status: {status}')
            if status == 'running' or status == 'paused':
                self._parse_runtime_response(response)
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                self.log(
                    'info', f'No existing runtime found for session ID: {self.sid}'
                )
                return False
            self.log(
                'error', f'Error while looking for remote runtime: {e}', exc_info=True
            )
            raise
        except httpx.HTTPError as e:
            self.log(
                'error', f'Error while looking for remote runtime: {e}', exc_info=True
            )
            raise
        except json.decoder.JSONDecodeError as e:
            self.log(
                'error',
                f'Invalid JSON response from runtime API: {e}. URL: {self.config.sandbox.remote_runtime_api_url}/sessions/{self.sid}. Response: {response}',
                exc_info=True,
            )
            raise

        if status == 'running':
            self.log('info', 'Found existing runtime in running state')
            return True
        elif status == 'stopped':
            self.log('info', 'Found existing runtime, but it is stopped')
            return False
        elif status == 'paused':
            self.log(
                'info', 'Found existing runtime in paused state, attempting to resume'
            )
            try:
                self._resume_runtime()
                self.log('info', 'Successfully resumed paused runtime')
                return True
            except Exception as e:
                self.log(
                    'error', f'Failed to resume paused runtime: {e}', exc_info=True
                )
                # Return false to indicate we couldn't use the existing runtime
                return False
        else:
            self.log('error', f'Invalid response from runtime API: {data}')
            return False