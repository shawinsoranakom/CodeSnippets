def send_message(self, message: str = "", **kwargs: Any) -> None:
        """Send a message to a user."""
        targets = kwargs.get(ATTR_TARGET, self.default_recipients)
        data = kwargs.get(ATTR_DATA) or {}

        clx_args = {ATTR_MESSAGE: message, ATTR_SENDER: self.sender}

        if ATTR_SENDER in data:
            clx_args[ATTR_SENDER] = data[ATTR_SENDER]

        if not targets:
            _LOGGER.error("At least 1 target is required")
            return

        try:
            for target in targets:
                result: MtBatchTextSmsResult = self.client.create_text_message(
                    clx_args[ATTR_SENDER], target, clx_args[ATTR_MESSAGE]
                )
                batch_id = result.batch_id
                _LOGGER.debug(
                    'Successfully sent SMS to "%s" (batch_id: %s)', target, batch_id
                )
        except ErrorResponseException as ex:
            _LOGGER.error(
                "Caught ErrorResponseException. Response code: %s (%s)",
                ex.error_code,
                ex,
            )
        except NotFoundException as ex:
            _LOGGER.error("Caught NotFoundException (request URL: %s)", ex.url)
        except UnauthorizedException as ex:
            _LOGGER.error(
                "Caught UnauthorizedException (service plan: %s)", ex.service_plan_id
            )
        except UnexpectedResponseException as ex:
            _LOGGER.error("Caught UnexpectedResponseException: %s", ex)