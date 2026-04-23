async def test_form_multiple_sites(
    hass: HomeAssistant,
    mock_omada_client: MagicMock,
    mock_setup_entry: MagicMock,
) -> None:
    """Test we get the form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {}

    mock_omada_client.get_sites.return_value = [
        OmadaSite("Site 1", "first"),
        OmadaSite("Site 2", "second"),
    ]

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        MOCK_USER_DATA,
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "site"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            "site": "second",
        },
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "OC200 (Site 2)"
    assert result["data"] == {
        "host": "https://fake.omada.host",
        "verify_ssl": True,
        "site": "second",
        "username": "test-username",
        "password": "test-password",
    }
    assert len(mock_setup_entry.mock_calls) == 1