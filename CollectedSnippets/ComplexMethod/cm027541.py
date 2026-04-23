async def inner(self: _SomaEntityT) -> dict:
        response = {}
        try:
            response_from_api = await api_call(self)
        except RequestException:
            if self.api_is_available:
                _LOGGER.warning("Connection to SOMA Connect failed")
                self.api_is_available = False
        else:
            if not self.api_is_available:
                self.api_is_available = True
                _LOGGER.info("Connection to SOMA Connect succeeded")

            if not is_api_response_success(response_from_api):
                if self.is_available:
                    self.is_available = False
                    _LOGGER.warning(
                        (
                            "Device is unreachable (%s). Error while fetching the"
                            " state: %s"
                        ),
                        self.name,
                        response_from_api["msg"],
                    )
            else:
                if not self.is_available:
                    self.is_available = True
                    _LOGGER.info("Device %s is now reachable", self.name)
                response = response_from_api
        return response