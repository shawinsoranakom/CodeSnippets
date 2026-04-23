async def test_advanced_flows(
    hass: HomeAssistant,
    b2_fixture: BackblazeFixture,
    mock_config_entry: MockConfigEntry,
    flow_type: str,
    scenario: str,
) -> None:
    """Test reauthentication and reconfiguration flows."""
    mock_config_entry.add_to_hass(hass)

    if flow_type == "reauth":
        source = SOURCE_REAUTH
        step_name = "reauth_confirm"

        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": source, "entry_id": mock_config_entry.entry_id},
        )
        assert result.get("type") is FlowResultType.FORM
        assert result.get("step_id") == step_name

        if scenario == "success":
            config = {
                CONF_KEY_ID: b2_fixture.key_id,
                CONF_APPLICATION_KEY: b2_fixture.application_key,
            }
            result = await hass.config_entries.flow.async_configure(
                result["flow_id"], config
            )
            assert result.get("type") is FlowResultType.ABORT
            assert result.get("reason") == "reauth_successful"

        else:  # invalid_credentials
            config = {CONF_KEY_ID: "invalid", CONF_APPLICATION_KEY: "invalid"}
            result = await hass.config_entries.flow.async_configure(
                result["flow_id"], config
            )
            assert result.get("type") is FlowResultType.FORM
            assert result.get("errors") == {"base": "invalid_credentials"}

    elif flow_type == "reconfigure":
        source = SOURCE_RECONFIGURE
        step_name = "reconfigure"

        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": source, "entry_id": mock_config_entry.entry_id},
        )
        assert result.get("type") is FlowResultType.FORM
        assert result.get("step_id") == step_name

        if scenario == "success":
            config = {
                CONF_KEY_ID: b2_fixture.key_id,
                CONF_APPLICATION_KEY: b2_fixture.application_key,
                "bucket": "testBucket",
                "prefix": "new_prefix/",
            }
        elif scenario == "prefix_normalization":
            config = {
                CONF_KEY_ID: b2_fixture.key_id,
                CONF_APPLICATION_KEY: b2_fixture.application_key,
                "bucket": "testBucket",
                "prefix": "no_slash_prefix",
            }
        else:  # validation_error
            config = {
                CONF_KEY_ID: "invalid_key",
                CONF_APPLICATION_KEY: "invalid_app_key",
                "bucket": "invalid_bucket",
                "prefix": "",
            }

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], config
        )

        if scenario == "validation_error":
            assert result.get("type") is FlowResultType.FORM
            assert result.get("errors") == {"base": "invalid_credentials"}
        else:
            assert result.get("type") is FlowResultType.ABORT
            assert result.get("reason") == "reconfigure_successful"