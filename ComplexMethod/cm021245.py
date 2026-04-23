async def test_select_site_errors(
    hass: HomeAssistant,
    mock_vrm_client: AsyncMock,
    side_effect: Exception | None,
    return_value: Mock | None,
    expected_error: str,
) -> None:
    """Parametrized select_site error scenarios."""
    sites = [_make_site(1, "A"), _make_site(2, "B")]
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    flow_id = result["flow_id"]
    mock_vrm_client.users.list_sites = AsyncMock(return_value=sites)
    if side_effect is not None:
        mock_vrm_client.users.get_site = AsyncMock(side_effect=side_effect)
    else:
        mock_vrm_client.users.get_site = AsyncMock(return_value=return_value)
    res_intermediate = await hass.config_entries.flow.async_configure(
        flow_id, {CONF_API_TOKEN: "token"}
    )
    assert res_intermediate["step_id"] == "select_site"
    result = await hass.config_entries.flow.async_configure(
        flow_id, {CONF_SITE_ID: str(sites[0].id)}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "select_site"
    assert result["errors"] == {"base": expected_error}

    # Fix the error path by making get_site succeed and submit again
    good_site = _make_site(sites[0].id, sites[0].name)
    mock_vrm_client.users.get_site = AsyncMock(return_value=good_site)
    result_success = await hass.config_entries.flow.async_configure(
        flow_id, {CONF_SITE_ID: str(sites[0].id)}
    )
    assert result_success["type"] is FlowResultType.CREATE_ENTRY
    assert result_success["data"] == {
        CONF_API_TOKEN: "token",
        CONF_SITE_ID: good_site.id,
    }