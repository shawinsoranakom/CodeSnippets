async def _async_test_service(
        service,
        data,
        method,
        payload=None,
        domain=DOMAIN,
        failure_side_effect=HomeAssistantError,
    ):
        err_count = len([x for x in caplog.records if x.levelno == logging.ERROR])

        # success
        if method.startswith("async_"):
            mocked_method = AsyncMock()
        else:
            mocked_method = MagicMock()
        setattr(mocked_bulb, method, mocked_method)
        await hass.services.async_call(domain, service, data, blocking=True)
        if payload is None:
            mocked_method.assert_called_once()
        elif isinstance(payload, list):
            mocked_method.assert_called_once_with(*payload)
        else:
            mocked_method.assert_called_once_with(**payload)
        assert (
            len([x for x in caplog.records if x.levelno == logging.ERROR]) == err_count
        )

        # failure
        if failure_side_effect:
            if method.startswith("async_"):
                mocked_method = AsyncMock(side_effect=failure_side_effect)
            else:
                mocked_method = MagicMock(side_effect=failure_side_effect)
            setattr(mocked_bulb, method, mocked_method)
            with pytest.raises(failure_side_effect):
                await hass.services.async_call(domain, service, data, blocking=True)