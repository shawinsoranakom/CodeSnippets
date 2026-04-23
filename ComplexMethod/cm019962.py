async def test_zone_set_preset_mode(
    hass: HomeAssistant,
    zone_id: str,
    freezer: FrozenDateTimeFactory,
    snapshot: SnapshotAssertion,
) -> None:
    """Test SERVICE_SET_PRESET_MODE of an evohome heating zone."""

    freezer.move_to("2024-07-10T12:00:00Z")
    results = []

    # SERVICE_SET_PRESET_MODE: none
    with patch("evohomeasync2.zone.Zone.reset") as mock_fcn:
        await hass.services.async_call(
            CLIMATE_DOMAIN,
            SERVICE_SET_PRESET_MODE,
            {
                ATTR_ENTITY_ID: zone_id,
                ATTR_PRESET_MODE: "none",
            },
            blocking=True,
        )

        mock_fcn.assert_awaited_once_with()

    # SERVICE_SET_PRESET_MODE: permanent
    with patch("evohomeasync2.zone.Zone.set_temperature") as mock_fcn:
        await hass.services.async_call(
            CLIMATE_DOMAIN,
            SERVICE_SET_PRESET_MODE,
            {
                ATTR_ENTITY_ID: zone_id,
                ATTR_PRESET_MODE: "permanent",
            },
            blocking=True,
        )

        mock_fcn.assert_awaited_once()

        assert mock_fcn.await_args is not None  # mypy hint
        assert mock_fcn.await_args.args != ()  # current target temp
        assert mock_fcn.await_args.kwargs == {"until": None}

        results.append(mock_fcn.await_args.args)

    # SERVICE_SET_PRESET_MODE: temporary
    with patch("evohomeasync2.zone.Zone.set_temperature") as mock_fcn:
        await hass.services.async_call(
            CLIMATE_DOMAIN,
            SERVICE_SET_PRESET_MODE,
            {
                ATTR_ENTITY_ID: zone_id,
                ATTR_PRESET_MODE: "temporary",
            },
            blocking=True,
        )

        mock_fcn.assert_awaited_once()

        assert mock_fcn.await_args is not None  # mypy hint
        assert mock_fcn.await_args.args != ()  # current target temp
        assert mock_fcn.await_args.kwargs != {}  # next setpoint dtm

        results.append(mock_fcn.await_args.args)
        results.append(mock_fcn.await_args.kwargs)

    assert results == snapshot