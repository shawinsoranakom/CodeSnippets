async def test_chat_session_with_echo_and_continue_final_message(
    client: openai.AsyncOpenAI, test_case: TestCase
):
    saying: str = "Here is a common saying about apple. An apple a day, keeps"
    # test echo with continue_final_message parameter
    chat_completion = await client.chat.completions.create(
        model=test_case.model_name,
        messages=[
            {"role": "user", "content": "tell me a common saying"},
            {"role": "assistant", "content": saying},
        ],
        extra_body={
            "echo": test_case.echo,
            "continue_final_message": True,
            "add_generation_prompt": False,
        },
    )
    assert chat_completion.id is not None
    assert len(chat_completion.choices) == 1

    choice = chat_completion.choices[0]
    assert choice.finish_reason == "stop"

    message = choice.message
    if test_case.echo:
        assert message.content is not None and saying in message.content
    else:
        assert message.content is not None and saying not in message.content
    assert message.role == "assistant"