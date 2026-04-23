async def test_form_unknown_exception(
    hass: HomeAssistant,
    mock_setup_entry: MagicMock,
    api_version: int,
) -> None:
    """Test we handle unknown exception."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    # Simulate a transient error
    with patch(
        "homeassistant.components.hunterdouglas_powerview.util.Hub.query_firmware",
        side_effect=SyntaxError,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_HOST: "1.2.3.4"},
        )

    assert result2["type"] is FlowResultType.FORM
    assert result2["errors"] == {"base": "unknown"}

    # Now try again without the patch in place to make sure we can recover
    result2 = await hass.config_entries.flow.async_configure(
        result2["flow_id"],
        {CONF_HOST: "1.2.3.4"},
    )

    assert result2["type"] is FlowResultType.CREATE_ENTRY
    assert result2["title"] == f"Powerview Generation {api_version}"
    assert result2["data"] == {CONF_HOST: "1.2.3.4", CONF_API_VERSION: api_version}
    assert result2["result"].unique_id == MOCK_SERIAL

    assert len(mock_setup_entry.mock_calls) == 1