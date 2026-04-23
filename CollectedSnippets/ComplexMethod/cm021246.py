async def test_select_site_duplicate_aborts(
    hass: HomeAssistant, mock_vrm_client: AsyncMock
) -> None:
    """Selecting an already configured site aborts during the select step (multi-site)."""
    site_id = 555
    # Existing entry with same site id

    existing = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_API_TOKEN: "token", CONF_SITE_ID: site_id},
        unique_id=str(site_id),
        title="Existing",
    )
    existing.add_to_hass(hass)

    # Start flow and reach select_site
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    mock_vrm_client.users.list_sites = AsyncMock(
        return_value=[_make_site(site_id, "Dup"), _make_site(777, "Other")]
    )
    mock_vrm_client.users.get_site = AsyncMock()
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_API_TOKEN: "token2"}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "select_site"

    # Selecting the same site should abort before validation (get_site not called)
    res_abort = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_SITE_ID: str(site_id)}
    )
    assert res_abort["type"] is FlowResultType.ABORT
    assert res_abort["reason"] == "already_configured"
    assert mock_vrm_client.users.get_site.call_count == 0

    # Start a new flow selecting the other site to finish with a create entry
    result_new = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    other_site = _make_site(777, "Other")
    mock_vrm_client.users.list_sites = AsyncMock(return_value=[other_site])
    result_new2 = await hass.config_entries.flow.async_configure(
        result_new["flow_id"], {CONF_API_TOKEN: "token3"}
    )
    assert result_new2["type"] is FlowResultType.CREATE_ENTRY
    assert result_new2["data"] == {
        CONF_API_TOKEN: "token3",
        CONF_SITE_ID: other_site.id,
    }