def wrapped_call(*args: list[Any], **kwargs: Any) -> Any:
            MAX_RETRIES = 5

            TIMEOUT = 600
            timeout_at = time.monotonic() + TIMEOUT

            for attempt in range(MAX_RETRIES):
                if time.monotonic() > timeout_at:
                    raise TimeoutError(
                        f"Confluence call attempts took longer than {TIMEOUT} seconds."
                    )

                # we're relying more on the client to rate limit itself
                # and applying our own retries in a more specific set of circumstances
                try:
                    if credential_provider:
                        with credential_provider:
                            credentials, renewed = self._renew_credentials()
                            if renewed:
                                self._confluence = self._initialize_connection_helper(
                                    credentials, **self._kwargs
                                )
                            attr = getattr(self._confluence, name, None)
                            if attr is None:
                                # The underlying Confluence client doesn't have this attribute
                                raise AttributeError(
                                    f"'{type(self).__name__}' object has no attribute '{name}'"
                                )

                            return attr(*args, **kwargs)
                    else:
                        attr = getattr(self._confluence, name, None)
                        if attr is None:
                            # The underlying Confluence client doesn't have this attribute
                            raise AttributeError(
                                f"'{type(self).__name__}' object has no attribute '{name}'"
                            )

                        return attr(*args, **kwargs)

                except HTTPError as e:
                    delay_until = _handle_http_error(e, attempt)
                    logging.warning(
                        f"HTTPError in confluence call. "
                        f"Retrying in {delay_until} seconds..."
                    )
                    while time.monotonic() < delay_until:
                        # in the future, check a signal here to exit
                        time.sleep(1)
                except AttributeError as e:
                    # Some error within the Confluence library, unclear why it fails.
                    # Users reported it to be intermittent, so just retry
                    if attempt == MAX_RETRIES - 1:
                        raise e

                    logging.exception(
                        "Confluence Client raised an AttributeError. Retrying..."
                    )
                    time.sleep(5)