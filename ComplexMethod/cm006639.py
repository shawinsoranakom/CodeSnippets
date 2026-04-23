def test_graph_before_callback_event():
    """Test that before_callback_event generates the correct RunStartedEvent payload."""
    # Create a simple graph with two components and a flow_id
    chat_input = ChatInput(_id="chat_input")
    chat_output = ChatOutput(input_value="test", _id="chat_output")
    chat_output.set(sender_name=chat_input.message_response)
    graph = Graph(chat_input, chat_output, flow_id="test_flow_id")

    # Call before_callback_event
    event = graph.before_callback_event()

    # Assert the event is a RunStartedEvent
    assert isinstance(event, RunStartedEvent)

    # Assert the event has the correct run_id and thread_id
    assert event.run_id == graph._run_id
    assert event.thread_id == graph.flow_id
    assert event.thread_id == "test_flow_id"

    # Assert the raw_event contains metrics
    assert event.raw_event is not None
    assert isinstance(event.raw_event, dict)

    # Assert the raw_event contains timestamp
    assert "timestamp" in event.raw_event
    assert isinstance(event.raw_event["timestamp"], float)

    # Assert the raw_event contains total_components
    assert "total_components" in event.raw_event
    assert event.raw_event["total_components"] == len(graph.vertices)
    assert event.raw_event["total_components"] == 2