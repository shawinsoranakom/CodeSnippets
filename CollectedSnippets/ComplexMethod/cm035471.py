def _send_action_server_request_impl(
        self, method: str, url: str, **kwargs: Any
    ) -> httpx.Response:
        try:
            return super()._send_action_server_request(method, url, **kwargs)
        except httpx.TimeoutException:
            self.log(
                'error',
                f'No response received within the timeout period for url: {url}',
            )
            raise

        except httpx.HTTPError as e:
            if hasattr(e, 'response') and e.response.status_code in (404, 502, 504):
                if e.response.status_code == 404:
                    raise AgentRuntimeDisconnectedError(
                        f'Runtime is not responding. This may be temporary, please try again. Original error: {e}'
                    ) from e
                else:  # 502, 504
                    raise AgentRuntimeDisconnectedError(
                        f'Runtime is temporarily unavailable. This may be due to a restart or network issue, please try again. Original error: {e}'
                    ) from e
            elif hasattr(e, 'response') and e.response.status_code == 503:
                if self.config.sandbox.keep_runtime_alive:
                    self.log(
                        'info',
                        f'Runtime appears to be paused (503 response). Runtime ID: {self.runtime_id}, URL: {url}',
                    )
                    try:
                        self._resume_runtime()
                        self.log(
                            'info', 'Successfully resumed runtime after 503 response'
                        )
                        return super()._send_action_server_request(
                            method, url, **kwargs
                        )
                    except Exception as resume_error:
                        self.log(
                            'error',
                            f'Failed to resume runtime after 503 response: {resume_error}',
                            exc_info=True,
                        )
                        raise AgentRuntimeDisconnectedError(
                            f'Runtime is paused and could not be resumed. Original error: {e}, Resume error: {resume_error}'
                        ) from resume_error
                else:
                    self.log(
                        'info',
                        'Runtime appears to be paused (503 response) but keep_runtime_alive is False',
                    )
                    raise AgentRuntimeDisconnectedError(
                        f'Runtime is temporarily unavailable. This may be due to a restart or network issue, please try again. Original error: {e}'
                    ) from e
            else:
                raise e