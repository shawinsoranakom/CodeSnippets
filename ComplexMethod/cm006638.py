def test_graph_functional_start_end():
    chat_input = ChatInput(_id="chat_input")
    text_output = TextOutputComponent(_id="text_output")
    text_output.set(input_value=chat_input.message_response)
    chat_output = ChatOutput(input_value="test", _id="chat_output")
    chat_output.set(input_value=text_output.text_response)
    graph = Graph(chat_input, text_output)
    graph.prepare()
    # Now iterate through the graph
    # and check that the graph is running
    # correctly
    ids = ["chat_input", "text_output"]
    results = list(graph.start())

    assert len(results) == len(ids) + 1
    assert all(result.vertex.id in ids for result in results if hasattr(result, "vertex"))
    assert results[-1] == Finish()
    # Now, using the same components but different start and end components
    graph = Graph(chat_input, chat_output)
    graph.prepare()
    ids = ["chat_input", "chat_output", "text_output"]
    results = []
    for result in graph.start():
        results.append(result)

    assert len(results) == len(ids) + 1
    assert all(result.vertex.id in ids for result in results if hasattr(result, "vertex"))
    assert results[-1] == Finish()