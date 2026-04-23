async def test_multiple_workbenches_serialize_and_deserialize() -> None:
    workbenches: List[McpWorkbench] = [
        McpWorkbench(server_params=SseServerParams(url="http://test-url-1")),
        McpWorkbench(server_params=SseServerParams(url="http://test-url-2")),
    ]

    client = OpenAIChatCompletionClient(
        model="gpt-4o",
        api_key="API_KEY",
    )

    agent = AssistantAgent(
        name="test_multi",
        model_client=client,
        workbench=workbenches,
    )

    serialize = agent.dump_component()
    deserialized_agent: AssistantAgent = AssistantAgent.load_component(serialize)

    assert deserialized_agent.name == agent.name
    assert isinstance(deserialized_agent._workbench, list)  # type: ignore
    assert len(deserialized_agent._workbench) == len(workbenches)  # type: ignore

    for original, restored in zip(agent._workbench, deserialized_agent._workbench, strict=True):  # type: ignore
        assert isinstance(original, McpWorkbench)
        assert isinstance(restored, McpWorkbench)
        assert original._to_config() == restored._to_config()