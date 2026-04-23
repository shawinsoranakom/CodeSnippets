def retry_request():
            """Attempt to call request_func with retries, timeout, and optional threading."""
            t0 = time.time()  # Record the start time for the timeout
            response = None
            for i in range(retry + 1):
                if (time.time() - t0) > timeout:
                    LOGGER.warning(f"{PREFIX}Timeout for request reached. {HELP_MSG}")
                    break  # Timeout reached, exit loop

                response = request_func(*args, **kwargs)
                if response is None:
                    LOGGER.warning(f"{PREFIX}Received no response from the request. {HELP_MSG}")
                    time.sleep(2**i)  # Exponential backoff before retrying
                    continue  # Skip further processing and retry

                if progress_total:
                    self._show_upload_progress(progress_total, response)
                elif stream_response:
                    self._iterate_content(response)

                if HTTPStatus.OK <= response.status_code < HTTPStatus.MULTIPLE_CHOICES:
                    # if request related to metrics upload
                    if kwargs.get("metrics"):
                        self.metrics_upload_failed_queue = {}
                    return response  # Success, no need to retry

                if i == 0:
                    # Initial attempt, check status code and provide messages
                    message = self._get_failure_message(response, retry, timeout)

                    if verbose:
                        LOGGER.warning(f"{PREFIX}{message} {HELP_MSG} ({response.status_code})")

                if not self._should_retry(response.status_code):
                    LOGGER.warning(f"{PREFIX}Request failed. {HELP_MSG} ({response.status_code}")
                    break  # Not an error that should be retried, exit loop

                time.sleep(2**i)  # Exponential backoff for retries

            # if request related to metrics upload and exceed retries
            if response is None and kwargs.get("metrics"):
                self.metrics_upload_failed_queue.update(kwargs.get("metrics"))

            return response