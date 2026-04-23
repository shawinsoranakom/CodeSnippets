async def async_send_message(self, message: str = "", **kwargs: Any) -> None:
        """Send a message to a user."""
        data = {self._message_param_name: message}

        if self._title_param_name is not None:
            data[self._title_param_name] = kwargs.get(ATTR_TITLE, ATTR_TITLE_DEFAULT)

        if self._target_param_name is not None and ATTR_TARGET in kwargs:
            # Target is a list as of 0.29 and we don't want to break existing
            # integrations, so just return the first target in the list.
            data[self._target_param_name] = kwargs[ATTR_TARGET][0]

        if self._data_template or self._data:
            kwargs[ATTR_MESSAGE] = message

            def _data_template_creator(value: Any) -> Any:
                """Recursive template creator helper function."""
                if isinstance(value, list):
                    return [_data_template_creator(item) for item in value]
                if isinstance(value, dict):
                    return {
                        key: _data_template_creator(item) for key, item in value.items()
                    }
                if not isinstance(value, Template):
                    return value
                return value.async_render(kwargs, parse_result=False)

            if self._data:
                data.update(_data_template_creator(self._data))
            if self._data_template:
                data.update(_data_template_creator(self._data_template))

        websession = get_async_client(self._hass, self._verify_ssl)
        if self._method == "POST":
            response = await websession.post(
                self._resource,
                headers=self._headers,
                params=self._params,
                data=data,
                timeout=10,
                auth=self._auth or httpx.USE_CLIENT_DEFAULT,
            )
        elif self._method == "POST_JSON":
            response = await websession.post(
                self._resource,
                headers=self._headers,
                params=self._params,
                json=data,
                timeout=10,
                auth=self._auth or httpx.USE_CLIENT_DEFAULT,
            )
        else:  # default GET
            response = await websession.get(
                self._resource,
                headers=self._headers,
                params={**self._params, **data} if self._params else data,
                timeout=10,
                auth=self._auth,
            )

        if (
            response.status_code >= HTTPStatus.INTERNAL_SERVER_ERROR
            and response.status_code < 600
        ):
            _LOGGER.exception(
                "Server error. Response %d: %s:",
                response.status_code,
                response.reason_phrase,
            )
        elif (
            response.status_code >= HTTPStatus.BAD_REQUEST
            and response.status_code < HTTPStatus.INTERNAL_SERVER_ERROR
        ):
            _LOGGER.exception(
                "Client error. Response %d: %s:",
                response.status_code,
                response.reason_phrase,
            )
        elif (
            response.status_code >= HTTPStatus.OK
            and response.status_code < HTTPStatus.MULTIPLE_CHOICES
        ):
            _LOGGER.debug(
                "Success. Response %d: %s:",
                response.status_code,
                response.reason_phrase,
            )
        else:
            _LOGGER.debug(
                "Response %d: %s:", response.status_code, response.reason_phrase
            )