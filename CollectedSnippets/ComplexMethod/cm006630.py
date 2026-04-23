def test_vertex_before_callback_event():
    """Test that Vertex.before_callback_event generates the correct StepStartedEvent payload."""
    # Create a graph with a ChatInput component, which creates a vertex
    from lfx.graph import Graph

    chat_input = ChatInput(_id="test_vertex_id")
    chat_output = ChatInput(_id="output_id")  # Need two components for Graph
    graph = Graph(chat_input, chat_output, flow_id="test_flow")

    # Get the vertex from the graph
    vertex = graph.vertices[0]  # First vertex should be chat_input
    assert vertex.id == "test_vertex_id"

    # Call before_callback_event
    event = vertex.before_callback_event()

    # Assert the event is a StepStartedEvent
    assert isinstance(event, StepStartedEvent)

    # Assert the event has the correct step_name
    assert event.step_name == vertex.display_name

    # Assert the raw_event contains the langflow metrics
    assert event.raw_event is not None
    assert isinstance(event.raw_event, dict)
    assert "langflow" in event.raw_event

    # Assert the langflow metrics contain expected fields
    langflow_metrics = event.raw_event["langflow"]
    assert isinstance(langflow_metrics, dict)
    assert "timestamp" in langflow_metrics
    assert isinstance(langflow_metrics["timestamp"], float)
    assert "component_id" in langflow_metrics
    assert langflow_metrics["component_id"] == vertex.id
    assert langflow_metrics["component_id"] == "test_vertex_id"