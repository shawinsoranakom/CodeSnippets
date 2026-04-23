async def test_set_operation_mode(
    hass: HomeAssistant,
    dhw_id: str,
    freezer: FrozenDateTimeFactory,
    snapshot: SnapshotAssertion,
) -> None:
    """Test SERVICE_SET_OPERATION_MODE of an evohome DHW zone."""

    freezer.move_to("2024-07-10T11:55:00Z")
    results = []

    # SERVICE_SET_OPERATION_MODE: auto
    with patch("evohomeasync2.hotwater.HotWater.reset") as mock_fcn:
        await hass.services.async_call(
            WATER_HEATER_DOMAIN,
            SERVICE_SET_OPERATION_MODE,
            {
                ATTR_ENTITY_ID: dhw_id,
                ATTR_OPERATION_MODE: "auto",
            },
            blocking=True,
        )

        mock_fcn.assert_awaited_once_with()

    # SERVICE_SET_OPERATION_MODE: off (until next scheduled setpoint)
    with patch("evohomeasync2.hotwater.HotWater.set_off") as mock_fcn:
        await hass.services.async_call(
            WATER_HEATER_DOMAIN,
            SERVICE_SET_OPERATION_MODE,
            {
                ATTR_ENTITY_ID: dhw_id,
                ATTR_OPERATION_MODE: "off",
            },
            blocking=True,
        )

        mock_fcn.assert_awaited_once()

        assert mock_fcn.await_args is not None  # mypy hint
        assert mock_fcn.await_args.args == ()
        assert mock_fcn.await_args.kwargs != {}

        results.append(mock_fcn.await_args.kwargs)

    # SERVICE_SET_OPERATION_MODE: on (until next scheduled setpoint)
    with patch("evohomeasync2.hotwater.HotWater.set_on") as mock_fcn:
        await hass.services.async_call(
            WATER_HEATER_DOMAIN,
            SERVICE_SET_OPERATION_MODE,
            {
                ATTR_ENTITY_ID: dhw_id,
                ATTR_OPERATION_MODE: "on",
            },
            blocking=True,
        )

        mock_fcn.assert_awaited_once()

        assert mock_fcn.await_args is not None  # mypy hint
        assert mock_fcn.await_args.args == ()
        assert mock_fcn.await_args.kwargs != {}

        results.append(mock_fcn.await_args.kwargs)

    assert results == snapshot