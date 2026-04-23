def close(self) -> None:
        if self.attach_to_existing:
            super().close()
            return
        if self.config.sandbox.keep_runtime_alive:
            if self.config.sandbox.pause_closed_runtimes:
                try:
                    if not self._runtime_closed:
                        self._send_runtime_api_request(
                            'POST',
                            f'{self.config.sandbox.remote_runtime_api_url}/pause',
                            json={'runtime_id': self.runtime_id},
                        )
                        self.log('info', 'Runtime paused.')
                except Exception as e:
                    self.log('error', f'Unable to pause runtime: {str(e)}')
                    raise e
            super().close()
            return
        try:
            if not self._runtime_closed:
                self._send_runtime_api_request(
                    'POST',
                    f'{self.config.sandbox.remote_runtime_api_url}/stop',
                    json={'runtime_id': self.runtime_id},
                )
                self.log('info', 'Runtime stopped.')
        except Exception as e:
            self.log('error', f'Unable to stop runtime: {str(e)}')
            raise e
        finally:
            super().close()