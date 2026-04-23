def test_construct_single_message_from_response_item(self):
        item = ResponseReasoningItem(
            id="lol",
            summary=[],
            type="reasoning",
            content=[
                Content(
                    text="Leroy Jenkins",
                    type="reasoning_text",
                )
            ],
            encrypted_content=None,
            status=None,
        )
        formatted_item = _construct_single_message_from_response_item(item)
        assert formatted_item["role"] == "assistant"
        assert formatted_item["reasoning"] == "Leroy Jenkins"

        item = ResponseReasoningItem(
            id="lol",
            summary=[
                Summary(
                    text='Hmm, the user has just started with a simple "Hello,"',
                    type="summary_text",
                )
            ],
            type="reasoning",
            content=None,
            encrypted_content=None,
            status=None,
        )

        formatted_item = _construct_single_message_from_response_item(item)
        assert formatted_item["role"] == "assistant"
        assert (
            formatted_item["reasoning"]
            == 'Hmm, the user has just started with a simple "Hello,"'
        )

        tool_call_output = ResponseFunctionToolCallOutputItem(
            id="temp_id",
            type="function_call_output",
            call_id="temp",
            output="1234",
            status="completed",
        )
        formatted_item = _construct_single_message_from_response_item(tool_call_output)
        assert formatted_item["role"] == "tool"
        assert formatted_item["content"] == "1234"
        assert formatted_item["tool_call_id"] == "temp"

        item = ResponseReasoningItem(
            id="lol",
            summary=[],
            type="reasoning",
            content=None,
            encrypted_content="TOP_SECRET_MESSAGE",
            status=None,
        )
        with pytest.raises(ValueError):
            _construct_single_message_from_response_item(item)

        output_item = ResponseOutputMessage(
            id="msg_bf585bbbe3d500e0",
            content=[
                ResponseOutputText(
                    annotations=[],
                    text="dongyi",
                    type="output_text",
                    logprobs=None,
                )
            ],
            role="assistant",
            status="completed",
            type="message",
        )

        formatted_item = _construct_single_message_from_response_item(output_item)
        assert formatted_item["role"] == "assistant"
        assert formatted_item["content"] == "dongyi"