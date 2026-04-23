async def test_hmip_climate_services(
    hass: HomeAssistant, mock_hap_with_service
) -> None:
    """Test HomematicipHeatingGroup."""

    home = mock_hap_with_service.home

    await hass.services.async_call(
        "homematicip_cloud",
        "activate_eco_mode_with_duration",
        {"duration": 60, "accesspoint_id": HAPID},
        blocking=True,
    )
    assert home.mock_calls[-1][0] == "activate_absence_with_duration_async"
    assert home.mock_calls[-1][1] == (60,)
    assert len(home._connection.mock_calls) == 1

    await hass.services.async_call(
        "homematicip_cloud",
        "activate_eco_mode_with_duration",
        {"duration": 60},
        blocking=True,
    )
    assert home.mock_calls[-1][0] == "activate_absence_with_duration_async"
    assert home.mock_calls[-1][1] == (60,)
    assert len(home._connection.mock_calls) == 2

    await hass.services.async_call(
        "homematicip_cloud",
        "activate_eco_mode_with_period",
        {"endtime": "2019-02-17 14:00", "accesspoint_id": HAPID},
        blocking=True,
    )
    assert home.mock_calls[-1][0] == "activate_absence_with_period_async"
    assert home.mock_calls[-1][1] == (datetime.datetime(2019, 2, 17, 14, 0),)
    assert len(home._connection.mock_calls) == 3

    await hass.services.async_call(
        "homematicip_cloud",
        "activate_eco_mode_with_period",
        {"endtime": "2019-02-17 14:00"},
        blocking=True,
    )
    assert home.mock_calls[-1][0] == "activate_absence_with_period_async"
    assert home.mock_calls[-1][1] == (datetime.datetime(2019, 2, 17, 14, 0),)
    assert len(home._connection.mock_calls) == 4

    await hass.services.async_call(
        "homematicip_cloud",
        "activate_vacation",
        {"endtime": "2019-02-17 14:00", "temperature": 18.5, "accesspoint_id": HAPID},
        blocking=True,
    )
    assert home.mock_calls[-1][0] == "activate_vacation_async"
    assert home.mock_calls[-1][1] == (datetime.datetime(2019, 2, 17, 14, 0), 18.5)
    assert len(home._connection.mock_calls) == 5

    await hass.services.async_call(
        "homematicip_cloud",
        "activate_vacation",
        {"endtime": "2019-02-17 14:00", "temperature": 18.5},
        blocking=True,
    )
    assert home.mock_calls[-1][0] == "activate_vacation_async"
    assert home.mock_calls[-1][1] == (datetime.datetime(2019, 2, 17, 14, 0), 18.5)
    assert len(home._connection.mock_calls) == 6

    await hass.services.async_call(
        "homematicip_cloud",
        "deactivate_eco_mode",
        {"accesspoint_id": HAPID},
        blocking=True,
    )
    assert home.mock_calls[-1][0] == "deactivate_absence_async"
    assert home.mock_calls[-1][1] == ()
    assert len(home._connection.mock_calls) == 7

    await hass.services.async_call(
        "homematicip_cloud", "deactivate_eco_mode", blocking=True
    )
    assert home.mock_calls[-1][0] == "deactivate_absence_async"
    assert home.mock_calls[-1][1] == ()
    assert len(home._connection.mock_calls) == 8

    await hass.services.async_call(
        "homematicip_cloud",
        "deactivate_vacation",
        {"accesspoint_id": HAPID},
        blocking=True,
    )
    assert home.mock_calls[-1][0] == "deactivate_vacation_async"
    assert home.mock_calls[-1][1] == ()
    assert len(home._connection.mock_calls) == 9

    await hass.services.async_call(
        "homematicip_cloud", "deactivate_vacation", blocking=True
    )
    assert home.mock_calls[-1][0] == "deactivate_vacation_async"
    assert home.mock_calls[-1][1] == ()
    assert len(home._connection.mock_calls) == 10

    not_existing_hap_id = "5555F7110000000000000001"
    with pytest.raises(ServiceValidationError) as excinfo:
        await hass.services.async_call(
            "homematicip_cloud",
            "deactivate_vacation",
            {"accesspoint_id": not_existing_hap_id},
            blocking=True,
        )
    assert excinfo.value.translation_domain == DOMAIN
    assert excinfo.value.translation_key == "access_point_not_found"
    # There is no further call on connection.
    assert len(home._connection.mock_calls) == 10