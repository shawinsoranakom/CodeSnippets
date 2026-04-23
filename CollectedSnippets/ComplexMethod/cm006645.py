async def test_graph_functional_start_state_update(self):
        chat_input = ChatInput(_id="chat_input", session_id="test", input_value="test")
        chat_output = ChatOutput(input_value="test", _id="chat_output", session_id="test")
        chat_output.set(sender_name=chat_input.message_response)
        chat_state_model = create_state_model(model_name="ChatState", message=chat_output.message_response)()
        assert chat_state_model.__class__.__name__ == "ChatState"
        assert chat_state_model.message is UNDEFINED

        graph = Graph(chat_input, chat_output)
        graph.prepare()
        # Now iterate through the graph
        # and check that the graph is running
        # correctly
        ids = ["chat_input", "chat_output"]
        results = [result async for result in graph.async_start()]

        assert len(results) == 3
        assert all(result.vertex.id in ids for result in results if hasattr(result, "vertex"))
        assert results[-1] == Finish()

        assert chat_state_model.__class__.__name__ == "ChatState"
        assert hasattr(chat_state_model.message, "get_text")
        assert chat_state_model.message.get_text() == "test"