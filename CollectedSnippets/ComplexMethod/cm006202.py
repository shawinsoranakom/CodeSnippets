async def test_default():
    outputs = await run_single_component(ChatInput, run_input="hello")
    assert isinstance(outputs["message"], Message)
    assert outputs["message"].text == "hello"
    assert outputs["message"].sender == "User"
    assert outputs["message"].sender_name == "User"

    outputs = await run_single_component(ChatInput, run_input="")
    assert isinstance(outputs["message"], Message)
    assert outputs["message"].text == ""
    assert outputs["message"].sender == "User"
    assert outputs["message"].sender_name == "User"