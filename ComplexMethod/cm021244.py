async def test_full_flow_success(
    hass: HomeAssistant, mock_setup_entry: AsyncMock, mock_vrm_client: AsyncMock
) -> None:
    """Test the 2-step flow: token -> select site -> create entry."""
    site1 = _make_site(123456, "ESS")
    site2 = _make_site(987654, "Cabin")

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {}

    mock_vrm_client.users.list_sites = AsyncMock(return_value=[site2, site1])
    mock_vrm_client.users.get_site = AsyncMock(return_value=site1)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_API_TOKEN: "test_token"}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "select_site"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_SITE_ID: str(site1.id)}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == f"VRM for {site1.name}"
    assert result["data"] == {
        CONF_API_TOKEN: "test_token",
        CONF_SITE_ID: site1.id,
    }
    assert mock_setup_entry.call_count == 1