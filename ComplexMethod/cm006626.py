def test_process_flow_one_group(one_grouped_chat_json_flow):
    grouped_chat_data = json.loads(one_grouped_chat_json_flow).get("data")
    # There should be only one node
    assert len(grouped_chat_data["nodes"]) == 1
    # Get the node, it should be a group node
    group_node = grouped_chat_data["nodes"][0]
    node_data = group_node["data"]["node"]
    assert node_data.get("flow") is not None
    template_data = node_data["template"]
    assert any("openai_api_key" in key for key in template_data)
    # Get the openai_api_key dict
    openai_api_key = next(
        (template_data[key] for key in template_data if "openai_api_key" in key),
        None,
    )
    assert openai_api_key is not None
    assert openai_api_key["value"] == "test"

    processed_flow = process_flow(grouped_chat_data)
    assert processed_flow is not None
    assert isinstance(processed_flow, dict)
    assert "nodes" in processed_flow
    assert "edges" in processed_flow

    # Now get the node that has ChatOpenAI in its id
    chat_openai_node = next((node for node in processed_flow["nodes"] if "ChatOpenAI" in node["id"]), None)
    assert chat_openai_node is not None
    assert chat_openai_node["data"]["node"]["template"]["openai_api_key"]["value"] == "test"