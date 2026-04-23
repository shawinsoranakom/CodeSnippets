def test_ungroup_node(grouped_chat_json_flow):
    grouped_chat_data = json.loads(grouped_chat_json_flow).get("data")
    group_node = grouped_chat_data["nodes"][2]  # Assuming the first node is a group node
    base_flow = copy.deepcopy(grouped_chat_data)
    ungroup_node(group_node["data"], base_flow)
    # after ungroup_node is called, the base_flow and grouped_chat_data should be different
    assert base_flow != grouped_chat_data
    # assert node 2 is not a group node anymore
    assert base_flow["nodes"][2]["data"]["node"].get("flow") is None
    # assert the edges are updated
    assert len(base_flow["edges"]) > len(grouped_chat_data["edges"])
    assert base_flow["edges"][0]["source"] == "ConversationBufferMemory-kUMif"
    assert base_flow["edges"][0]["target"] == "LLMChain-2P369"
    assert base_flow["edges"][1]["source"] == "PromptTemplate-Wjk4g"
    assert base_flow["edges"][1]["target"] == "LLMChain-2P369"
    assert base_flow["edges"][2]["source"] == "ChatOpenAI-rUJ1b"
    assert base_flow["edges"][2]["target"] == "LLMChain-2P369"