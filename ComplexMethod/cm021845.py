async def test_hmip_set_home_cooling_mode(
    hass: HomeAssistant, mock_hap_with_service
) -> None:
    """Test HomematicipSetHomeCoolingMode."""

    home = mock_hap_with_service.home

    await hass.services.async_call(
        "homematicip_cloud",
        "set_home_cooling_mode",
        {"accesspoint_id": HAPID, "cooling": False},
        blocking=True,
    )
    assert home.mock_calls[-1][0] == "set_cooling_async"
    assert home.mock_calls[-1][1] == (False,)
    assert len(home._connection.mock_calls) == 1

    await hass.services.async_call(
        "homematicip_cloud",
        "set_home_cooling_mode",
        {"accesspoint_id": HAPID, "cooling": True},
        blocking=True,
    )
    assert home.mock_calls[-1][0] == "set_cooling_async"
    assert home.mock_calls[-1][1]
    assert len(home._connection.mock_calls) == 2

    await hass.services.async_call(
        "homematicip_cloud", "set_home_cooling_mode", blocking=True
    )
    assert home.mock_calls[-1][0] == "set_cooling_async"
    assert home.mock_calls[-1][1]
    assert len(home._connection.mock_calls) == 3

    not_existing_hap_id = "5555F7110000000000000001"
    with pytest.raises(ServiceValidationError) as excinfo:
        await hass.services.async_call(
            "homematicip_cloud",
            "set_home_cooling_mode",
            {"accesspoint_id": not_existing_hap_id, "cooling": True},
            blocking=True,
        )
    assert excinfo.value.translation_domain == DOMAIN
    assert excinfo.value.translation_key == "access_point_not_found"
    # There is no further call on connection.
    assert len(home._connection.mock_calls) == 3