async def make_mock_api(
    api_call_side_effects: dict[str, Any],
    brand: Brand = Brand.YALE_GLOBAL,
) -> ApiAsync:
    """Make a mock ApiAsync instance."""
    api_instance = MagicMock(name="Api", brand=brand)

    if api_call_side_effects["get_lock_detail"]:
        type(api_instance).async_get_lock_detail = AsyncMock(
            side_effect=api_call_side_effects["get_lock_detail"]
        )

    if api_call_side_effects["get_operable_locks"]:
        type(api_instance).async_get_operable_locks = AsyncMock(
            side_effect=api_call_side_effects["get_operable_locks"]
        )

    if api_call_side_effects["get_doorbells"]:
        type(api_instance).async_get_doorbells = AsyncMock(
            side_effect=api_call_side_effects["get_doorbells"]
        )

    if api_call_side_effects["get_doorbell_detail"]:
        type(api_instance).async_get_doorbell_detail = AsyncMock(
            side_effect=api_call_side_effects["get_doorbell_detail"]
        )

    if api_call_side_effects["get_house_activities"]:
        type(api_instance).async_get_house_activities = AsyncMock(
            side_effect=api_call_side_effects["get_house_activities"]
        )

    if api_call_side_effects["lock_return_activities"]:
        type(api_instance).async_lock_return_activities = AsyncMock(
            side_effect=api_call_side_effects["lock_return_activities"]
        )

    if api_call_side_effects["unlock_return_activities"]:
        type(api_instance).async_unlock_return_activities = AsyncMock(
            side_effect=api_call_side_effects["unlock_return_activities"]
        )

    if api_call_side_effects["async_unlatch_return_activities"]:
        type(api_instance).async_unlatch_return_activities = AsyncMock(
            side_effect=api_call_side_effects["async_unlatch_return_activities"]
        )

    api_instance.async_unlock_async = AsyncMock()
    api_instance.async_lock_async = AsyncMock()
    api_instance.async_status_async = AsyncMock()
    api_instance.async_get_user = AsyncMock(return_value={"UserID": "abc"})
    api_instance.async_unlatch_async = AsyncMock()
    api_instance.async_unlatch = AsyncMock()
    api_instance.async_add_websocket_subscription = AsyncMock()

    # Mock capabilities endpoint
    async def mock_get_lock_capabilities(token, serial_number):
        """Mock the capabilities endpoint response."""
        capabilities = _LOCK_CAPABILITIES.get(serial_number, _DEFAULT_CAPABILITIES)
        return {"lock": capabilities}

    api_instance.async_get_lock_capabilities = AsyncMock(
        side_effect=mock_get_lock_capabilities
    )

    return api_instance