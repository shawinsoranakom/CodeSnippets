async def test_async_update_title_placeholders(hass: HomeAssistant) -> None:
    """Test async_update_title_placeholders updates context and notifies listeners."""

    class TestFlow(config_entries.ConfigFlow):
        """Test flow."""

        VERSION = 1

        async def async_step_user(self, user_input=None):
            """Test user step."""
            self.context["title_placeholders"] = {"initial": "value"}
            return self.async_show_form(step_id="user")

    mock_integration(hass, MockModule("comp"))
    mock_platform(hass, "comp.config_flow", None)

    with patch.dict(config_entries.HANDLERS, {"comp": TestFlow}):
        result = await hass.config_entries.flow.async_init(
            "comp", context={"source": config_entries.SOURCE_USER}
        )
        assert result["type"] is FlowResultType.FORM

        # Get the flow to check initial title_placeholders
        flow = hass.config_entries.flow.async_get(result["flow_id"])
        assert flow["context"]["title_placeholders"] == {"initial": "value"}

        # Get the flow instance to call methods
        flow_instance = hass.config_entries.flow._progress[result["flow_id"]]

        # Capture events to verify frontend notification
        events = async_capture_events(
            hass, data_entry_flow.EVENT_DATA_ENTRY_FLOW_PROGRESSED
        )

        # Update title placeholders
        flow_instance.async_update_title_placeholders({"name": "updated"})
        await hass.async_block_till_done()

        # Verify placeholders were updated (preserving existing values)
        flow = hass.config_entries.flow.async_get(result["flow_id"])
        assert flow["context"]["title_placeholders"] == {
            "initial": "value",
            "name": "updated",
        }

        # Verify frontend was notified
        assert len(events) == 1
        assert events[0].data == {
            "handler": "comp",
            "flow_id": result["flow_id"],
            "refresh": True,
        }

        # Update again with overlapping key
        flow_instance.async_update_title_placeholders(
            {"initial": "new_value", "another": "key"}
        )
        await hass.async_block_till_done()

        # Verify placeholders were updated correctly
        flow = hass.config_entries.flow.async_get(result["flow_id"])
        assert flow["context"]["title_placeholders"] == {
            "initial": "new_value",
            "name": "updated",
            "another": "key",
        }

        # Verify frontend was notified again
        assert len(events) == 2