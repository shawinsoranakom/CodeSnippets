async def _test_service(
    hass: HomeAssistant,
    entity_id,
    ha_service_name,
    androidtv_method,
    additional_service_data=None,
    expected_call_args=None,
) -> None:
    """Test generic Android media player entity service."""
    if expected_call_args is None:
        expected_call_args = [None]

    service_data = {ATTR_ENTITY_ID: entity_id}
    if additional_service_data:
        service_data.update(additional_service_data)

    androidtv_patch = (
        "androidtv.androidtv_async.AndroidTVAsync"
        if "android" in entity_id
        else "firetv.firetv_async.FireTVAsync"
    )
    with patch(f"androidtv.{androidtv_patch}.{androidtv_method}") as api_call:
        await hass.services.async_call(
            REMOTE_DOMAIN,
            ha_service_name,
            service_data=service_data,
            blocking=True,
        )
        assert api_call.called
        assert api_call.call_count == len(expected_call_args)
        expected_calls = [call(s) if s else call() for s in expected_call_args]
        assert api_call.call_args_list == expected_calls