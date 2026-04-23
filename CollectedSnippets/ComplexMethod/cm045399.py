async def test_graph_flow_serialize_deserialize() -> None:
    client_a = ReplayChatCompletionClient(list(map(str, range(10))))
    client_b = ReplayChatCompletionClient(list(map(str, range(10))))
    a = AssistantAgent("A", model_client=client_a)
    b = AssistantAgent("B", model_client=client_b)

    builder = DiGraphBuilder()
    builder.add_node(a).add_node(b)
    builder.add_edge(a, b)
    builder.set_entry_point(a)

    team = GraphFlow(
        participants=builder.get_participants(),
        graph=builder.build(),
        runtime=None,
    )

    serialized = team.dump_component()
    deserialized_team = GraphFlow.load_component(serialized)
    serialized_deserialized = deserialized_team.dump_component()

    results = await team.run(task="Start")
    de_results = await deserialized_team.run(task="Start")

    assert serialized == serialized_deserialized
    assert compare_task_results(results, de_results)
    assert results.stop_reason is not None
    assert results.stop_reason == de_results.stop_reason
    assert compare_message_lists(results.messages, de_results.messages)
    assert isinstance(results.messages[0], TextMessage)
    assert results.messages[0].source == "user"
    assert results.messages[0].content == "Start"
    assert isinstance(results.messages[1], TextMessage)
    assert results.messages[1].source == "A"
    assert results.messages[1].content == "0"
    assert isinstance(results.messages[2], TextMessage)
    assert results.messages[2].source == "B"
    assert results.messages[2].content == "0"
    # No stop agent message should appear in the conversation
    assert all(not isinstance(m, StopMessage) for m in results.messages)
    assert results.stop_reason is not None