def test_generates_valid_json_patch(self):
        reset_working_flow()
        flow = _build_test_flow()
        init_working_flow(flow, "test-flow-id")
        comp_id = _get_component_id(flow, "ChatInput")

        tool = ProposeFieldEdit()
        tool.set(component_id=comp_id, field_name="input_value", new_value="hello world")
        result = tool.propose_field_edit()

        assert "error" not in result.data
        events = drain_flow_events()
        assert len(events) == 1

        event = events[0]
        assert event["action"] == "edit_field"
        assert event["component_id"] == comp_id
        assert event["field"] == "input_value"
        assert event["new_value"] == "hello world"
        assert "patch" in event

        # Verify the patch is valid JSON Patch
        patch = jsonpatch.JsonPatch(event["patch"])
        assert len(list(patch)) == 1