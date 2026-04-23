async def _request_code(self) -> dict:
        assert self._client
        errors: dict[str, str] = {}
        try:
            await self._client.request_code_v4()
        except RoborockAccountDoesNotExist:
            errors["base"] = "invalid_email"
        except RoborockUrlException:
            errors["base"] = "unknown_url"
        except RoborockInvalidEmail:
            errors["base"] = "invalid_email_format"
        except RoborockTooFrequentCodeRequests:
            errors["base"] = "too_frequent_code_requests"
        except RoborockException:
            _LOGGER.exception("Unexpected exception")
            errors["base"] = "unknown_roborock"
        except Exception:
            _LOGGER.exception("Unexpected exception")
            errors["base"] = "unknown"
        return errors