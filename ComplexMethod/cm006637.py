def test_graph_state_model_json_schema():
    chat_input = ChatInput(_id="chat_input")
    chat_input.set(input_value="Test Sender Name")
    chat_output = ChatOutput(input_value="test", _id="chat_output")
    chat_output.set(sender_name=chat_input.message_response)

    graph = Graph(chat_input, chat_output)
    graph.prepare()

    graph_state_model: BaseModel = create_state_model_from_graph(graph)()
    json_schema = graph_state_model.model_json_schema(mode="serialization")

    # Test main schema structure
    assert json_schema["title"] == "GraphStateModel"
    assert json_schema["type"] == "object"
    assert set(json_schema["required"]) == {"chat_input", "chat_output"}

    # Test chat_input and chat_output properties
    for prop in ["chat_input", "chat_output"]:
        assert prop in json_schema["properties"]
        assert json_schema["properties"][prop]["allOf"][0]["$ref"].startswith("#/$defs/")
        assert json_schema["properties"][prop]["readOnly"] is True

    # Test $defs
    assert set(json_schema["$defs"].keys()) == {"ChatInputStateModel", "ChatOutputStateModel", "Image", "Message"}

    # Test ChatInputStateModel and ChatOutputStateModel
    for model in ["ChatInputStateModel", "ChatOutputStateModel"]:
        assert json_schema["$defs"][model]["type"] == "object"
        assert json_schema["$defs"][model]["title"] == model
        assert "message" in json_schema["$defs"][model]["properties"]
        assert json_schema["$defs"][model]["properties"]["message"]["allOf"][0]["$ref"] == "#/$defs/Message"
        assert json_schema["$defs"][model]["properties"]["message"]["readOnly"] is True
        assert json_schema["$defs"][model]["required"] == ["message"]

    # Test Message model
    message_props = json_schema["$defs"]["Message"]["properties"]
    assert set(message_props.keys()) == {
        "text_key",
        "data",
        "default_value",
        "text",
        "sender",
        "sender_name",
        "files",
        "session_id",
        "timestamp",
        "flow_id",
    }
    assert message_props["text_key"]["type"] == "string"
    assert message_props["data"]["type"] == "object"
    assert "anyOf" in message_props["default_value"]
    assert "anyOf" in message_props["files"]
    assert message_props["timestamp"]["type"] == "string"

    # Test Image model
    image_props = json_schema["$defs"]["Image"]["properties"]
    assert set(image_props.keys()) == {"path", "url"}
    for prop in ["path", "url"]:
        assert "anyOf" in image_props[prop]
        assert {"type": "string"} in image_props[prop]["anyOf"]
        assert {"type": "null"} in image_props[prop]["anyOf"]