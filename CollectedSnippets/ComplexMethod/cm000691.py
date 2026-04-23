async def test_orchestrator_function_signature(server: SpinTestServer):
    from backend.blocks.agent import AgentExecutorBlock
    from backend.blocks.basic import StoreValueBlock
    from backend.blocks.orchestrator import OrchestratorBlock
    from backend.data import graph

    test_user = await create_test_user()
    test_tool_graph = await create_graph(server, create_test_graph(), test_user)
    creds = await create_credentials(server, test_user)

    nodes = [
        graph.Node(
            block_id=OrchestratorBlock().id,
            input_default={
                "prompt": "Hello, World!",
                "credentials": creds,
            },
        ),
        graph.Node(
            block_id=AgentExecutorBlock().id,
            input_default={
                "graph_id": test_tool_graph.id,
                "graph_version": test_tool_graph.version,
                "input_schema": test_tool_graph.input_schema,
                "output_schema": test_tool_graph.output_schema,
            },
        ),
        graph.Node(
            block_id=StoreValueBlock().id,
        ),
    ]

    links = [
        graph.Link(
            source_id=nodes[0].id,
            sink_id=nodes[1].id,
            source_name="tools_^_sample_tool_input_1",
            sink_name="input_1",
        ),
        graph.Link(
            source_id=nodes[0].id,
            sink_id=nodes[1].id,
            source_name="tools_^_sample_tool_input_2",
            sink_name="input_2",
        ),
        graph.Link(
            source_id=nodes[0].id,
            sink_id=nodes[2].id,
            source_name="tools_^_store_value_input",
            sink_name="input",
        ),
    ]

    test_graph = graph.Graph(
        name="TestGraph",
        description="Test graph",
        nodes=nodes,
        links=links,
    )
    test_graph = await create_graph(server, test_graph, test_user)

    tool_functions = await OrchestratorBlock._create_tool_node_signatures(
        test_graph.nodes[0].id
    )
    assert tool_functions is not None, "Tool functions should not be None"

    assert (
        len(tool_functions) == 2
    ), f"Expected 2 tool functions, got {len(tool_functions)}"

    # Check the first tool function (testgraph)
    assert tool_functions[0]["type"] == "function"
    assert tool_functions[0]["function"]["name"] == "testgraph"
    assert tool_functions[0]["function"]["description"] == "Test graph description"
    assert "input_1" in tool_functions[0]["function"]["parameters"]["properties"]
    assert "input_2" in tool_functions[0]["function"]["parameters"]["properties"]

    # Check the second tool function (storevalueblock)
    assert tool_functions[1]["type"] == "function"
    assert tool_functions[1]["function"]["name"] == "storevalueblock"
    assert "input" in tool_functions[1]["function"]["parameters"]["properties"]
    assert (
        tool_functions[1]["function"]["parameters"]["properties"]["input"][
            "description"
        ]
        == "Trigger the block to produce the output. The value is only used when `data` is None."
    )