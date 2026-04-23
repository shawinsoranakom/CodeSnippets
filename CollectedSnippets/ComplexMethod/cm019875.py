async def test_errors(
    hass: HomeAssistant,
    mock_setup_entry: AsyncMock,
    mock_dio_chacon_client: AsyncMock,
    exception: Exception,
    expected: dict[str, str],
) -> None:
    """Test we handle any error."""
    mock_dio_chacon_client.get_user_id.side_effect = exception

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
        data={
            CONF_USERNAME: "nada",
            CONF_PASSWORD: "nadap",
        },
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == expected

    # Test of recover in normal state after correction of the 1st error
    mock_dio_chacon_client.get_user_id.side_effect = None
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_USERNAME: "dummylogin",
            CONF_PASSWORD: "dummypass",
        },
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Chacon DiO dummylogin"
    assert result["result"].unique_id == "dummy-user-id"
    assert result["data"] == {
        CONF_USERNAME: "dummylogin",
        CONF_PASSWORD: "dummypass",
    }