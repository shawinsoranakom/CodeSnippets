def test_graph_state_model_serialization():
    chat_input = ChatInput(_id="chat_input")
    chat_input.set(input_value="Test Sender Name", should_store_message=False)
    chat_output = ChatOutput(input_value="test", _id="chat_output")
    chat_output.set(sender_name=chat_input.message_response, should_store_message=False)

    graph = Graph(chat_input, chat_output)
    graph.prepare()
    # Now iterate through the graph
    # and check that the graph is running
    # correctly
    graph_state_model = create_state_model_from_graph(graph)()
    ids = ["chat_input", "chat_output"]
    results = list(graph.start())

    assert len(results) == 3
    assert all(result.vertex.id in ids for result in results if hasattr(result, "vertex"))
    assert results[-1] == Finish()

    assert graph_state_model.__class__.__name__ == "GraphStateModel"
    assert graph_state_model.chat_input.message.get_text() == "Test Sender Name"
    assert graph_state_model.chat_output.message.get_text() == "test"

    serialized_state_model = graph_state_model.model_dump()
    assert serialized_state_model["chat_input"]["message"]["text"] == "Test Sender Name"