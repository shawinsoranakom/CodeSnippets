async def test_user_not_authorizing_new_tokens_user_step_link_step(
    hass: HomeAssistant,
) -> None:
    """Test we handle NotAuthorizingNewTokens in user step and link step."""
    with (
        patch(
            "homeassistant.components.nanoleaf.config_flow.Nanoleaf",
            return_value=_mock_nanoleaf(authorize_error=Unauthorized()),
        ) as mock_nanoleaf,
        patch(
            "homeassistant.components.nanoleaf.async_setup_entry", return_value=True
        ) as mock_setup_entry,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        assert result["type"] is FlowResultType.FORM
        assert result["errors"] is None
        assert result["step_id"] == "user"
        assert not result["last_step"]

        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_HOST: TEST_HOST,
            },
        )
        assert result2["type"] is FlowResultType.FORM
        assert result2["errors"] is None
        assert result2["step_id"] == "link"

        result3 = await hass.config_entries.flow.async_configure(result["flow_id"])
        assert result3["type"] is FlowResultType.FORM
        assert result3["errors"] is None
        assert result3["step_id"] == "link"

        result4 = await hass.config_entries.flow.async_configure(result["flow_id"], {})
        assert result4["type"] is FlowResultType.FORM
        assert result4["errors"] == {"base": "not_allowing_new_tokens"}
        assert result4["step_id"] == "link"

        mock_nanoleaf.return_value.authorize.side_effect = None

        result5 = await hass.config_entries.flow.async_configure(result["flow_id"], {})
        assert result5["type"] is FlowResultType.CREATE_ENTRY
        assert result5["title"] == TEST_NAME
        assert result5["data"] == {
            CONF_HOST: TEST_HOST,
            CONF_TOKEN: TEST_TOKEN,
        }
        await hass.async_block_till_done()
        assert len(mock_setup_entry.mock_calls) == 1