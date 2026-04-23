async def test_full_flow_with_error(
    hass: HomeAssistant,
    mock_setup_entry: AsyncMock,
    mock_whois: MagicMock,
    snapshot: SnapshotAssertion,
    throw: Exception,
    reason: str,
) -> None:
    """Test the full user configuration flow with an error.

    This tests tests a full config flow, with an error happening; allowing
    the user to fix the error and try again.
    """
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    assert result.get("type") is FlowResultType.FORM
    assert result.get("step_id") == "user"

    mock_whois.side_effect = throw
    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_DOMAIN: "Example.com"},
    )

    assert result2.get("type") is FlowResultType.FORM
    assert result2.get("step_id") == "user"
    assert result2.get("errors") == {"base": reason}

    assert len(mock_setup_entry.mock_calls) == 0
    assert len(mock_whois.mock_calls) == 1

    mock_whois.side_effect = None
    result3 = await hass.config_entries.flow.async_configure(
        result2["flow_id"],
        user_input={CONF_DOMAIN: "Example.com"},
    )

    assert result3.get("type") is FlowResultType.CREATE_ENTRY
    assert result3 == snapshot

    assert len(mock_setup_entry.mock_calls) == 1
    assert len(mock_whois.mock_calls) == 2