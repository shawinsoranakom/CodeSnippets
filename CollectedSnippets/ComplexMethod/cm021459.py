async def test_service_mealplan(
    hass: HomeAssistant,
    mock_mealie_client: AsyncMock,
    mock_config_entry: MockConfigEntry,
    snapshot: SnapshotAssertion,
    freezer: FrozenDateTimeFactory,
) -> None:
    """Test the get_mealplan service."""

    await setup_integration(hass, mock_config_entry)

    freezer.move_to("2023-10-21")

    response = await hass.services.async_call(
        DOMAIN,
        SERVICE_GET_MEALPLAN,
        {ATTR_CONFIG_ENTRY_ID: mock_config_entry.entry_id},
        blocking=True,
        return_response=True,
    )
    assert mock_mealie_client.get_mealplans.call_args_list[1][0] == (
        date(2023, 10, 21),
        date(2023, 10, 21),
    )
    assert response == snapshot

    response = await hass.services.async_call(
        DOMAIN,
        SERVICE_GET_MEALPLAN,
        {
            ATTR_CONFIG_ENTRY_ID: mock_config_entry.entry_id,
            ATTR_START_DATE: "2023-10-22",
            ATTR_END_DATE: "2023-10-25",
        },
        blocking=True,
        return_response=True,
    )
    assert response
    assert mock_mealie_client.get_mealplans.call_args_list[2][0] == (
        date(2023, 10, 22),
        date(2023, 10, 25),
    )

    response = await hass.services.async_call(
        DOMAIN,
        SERVICE_GET_MEALPLAN,
        {
            ATTR_CONFIG_ENTRY_ID: mock_config_entry.entry_id,
            ATTR_START_DATE: "2023-10-19",
        },
        blocking=True,
        return_response=True,
    )
    assert response
    assert mock_mealie_client.get_mealplans.call_args_list[3][0] == (
        date(2023, 10, 19),
        date(2023, 10, 21),
    )

    response = await hass.services.async_call(
        DOMAIN,
        SERVICE_GET_MEALPLAN,
        {
            ATTR_CONFIG_ENTRY_ID: mock_config_entry.entry_id,
            ATTR_END_DATE: "2023-10-22",
        },
        blocking=True,
        return_response=True,
    )
    assert response
    assert mock_mealie_client.get_mealplans.call_args_list[4][0] == (
        date(2023, 10, 21),
        date(2023, 10, 22),
    )

    with pytest.raises(ServiceValidationError):
        await hass.services.async_call(
            DOMAIN,
            SERVICE_GET_MEALPLAN,
            {
                ATTR_CONFIG_ENTRY_ID: mock_config_entry.entry_id,
                ATTR_START_DATE: "2023-10-22",
                ATTR_END_DATE: "2023-10-19",
            },
            blocking=True,
            return_response=True,
        )