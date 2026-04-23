async def test_streaming(client: OpenAI, model_name: str, background: bool):
    # TODO: Add back when web search and code interpreter are available in CI
    prompts = [
        "tell me a story about a cat in 20 words",
        "What is 123 * 456? Use python to calculate the result.",
        # "When did Jensen found NVIDIA? Search it and answer the year only.",
    ]

    for prompt in prompts:
        stream = await client.responses.create(
            model=model_name,
            input=prompt,
            reasoning={"effort": "low"},
            tools=[
                # {
                #     "type": "web_search_preview"
                # },
                {"type": "code_interpreter", "container": {"type": "auto"}},
            ],
            stream=True,
            background=background,
            extra_body={"enable_response_messages": True},
        )

        current_item_id = ""
        current_content_index = -1

        events = []
        current_event_mode = None
        resp_id = None
        checked_response_completed = False

        async for event in stream:
            if event.type == "response.created":
                resp_id = event.response.id

            # Validate custom fields on response-level events
            if event.type in [
                "response.completed",
                "response.in_progress",
                "response.created",
            ]:
                assert "input_messages" in event.response.model_extra
                assert "output_messages" in event.response.model_extra
                if event.type == "response.completed":
                    # make sure the serialization of content works
                    for msg in event.response.model_extra["output_messages"]:
                        # make sure we can convert the messages back into harmony
                        Message.from_dict(msg)

                    for msg in event.response.model_extra["input_messages"]:
                        # make sure we can convert the messages back into harmony
                        Message.from_dict(msg)
                    checked_response_completed = True

            if current_event_mode != event.type:
                current_event_mode = event.type
                logger.debug("[%s] ", event.type)

            # Verify item IDs
            if event.type == "response.output_item.added":
                assert event.item.id != current_item_id
                current_item_id = event.item.id
            elif event.type in [
                "response.output_text.delta",
                "response.reasoning_text.delta",
            ]:
                assert event.item_id == current_item_id

            # Verify content indices
            if event.type in [
                "response.content_part.added",
                "response.reasoning_part.added",
            ]:
                assert event.content_index != current_content_index
                current_content_index = event.content_index
            elif event.type in [
                "response.output_text.delta",
                "response.reasoning_text.delta",
            ]:
                assert event.content_index == current_content_index

            events.append(event)

        assert len(events) > 0
        assert events[-1].response.output, "Final response should have output"
        assert checked_response_completed

        if background:
            starting_after = 5
            async with await client.responses.retrieve(
                response_id=resp_id, stream=True, starting_after=starting_after
            ) as replay_stream:
                counter = starting_after
                async for event in replay_stream:
                    counter += 1
                    assert event == events[counter]
            assert counter == len(events) - 1