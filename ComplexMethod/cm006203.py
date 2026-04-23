async def test_do_not_store_messages():
    session_id = "test-session-id"
    outputs = await run_single_component(
        ChatInput, inputs={"should_store_message": True}, run_input="hello", session_id=session_id
    )
    assert isinstance(outputs["message"], Message)
    assert outputs["message"].text == "hello"
    assert outputs["message"].session_id == session_id

    assert len(await aget_messages(session_id=session_id)) == 1

    session_id = "test-session-id-another"
    outputs = await run_single_component(
        ChatInput, inputs={"should_store_message": False}, run_input="hello", session_id=session_id
    )
    assert isinstance(outputs["message"], Message)
    assert outputs["message"].text == "hello"
    assert outputs["message"].session_id == session_id

    assert len(await aget_messages(session_id=session_id)) == 0