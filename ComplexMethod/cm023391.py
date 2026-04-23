async def test_add_friend_flow_already_configured_as_entry(
    hass: HomeAssistant, config_entry: MockConfigEntry
) -> None:
    """Test we abort add friend subentry flow when already configured as config entry."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        title="test-user",
        data={
            CONF_NPSSO: NPSSO_TOKEN,
        },
        unique_id=PSN_ID,
    )
    fren_config_entry = MockConfigEntry(
        domain=DOMAIN,
        title="PublicUniversalFriend",
        data={
            CONF_NPSSO: NPSSO_TOKEN,
        },
        unique_id="fren-psn-id",
    )

    config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(config_entry.entry_id)

    fren_config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(fren_config_entry.entry_id)
    await hass.async_block_till_done()

    assert config_entry.state is ConfigEntryState.LOADED

    result = await hass.config_entries.subentries.async_init(
        (config_entry.entry_id, "friend"),
        context={"source": SOURCE_USER},
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"],
        user_input={CONF_ACCOUNT_ID: "fren-psn-id"},
    )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured_as_entry"