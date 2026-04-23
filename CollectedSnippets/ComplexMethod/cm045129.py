async def test_add_name_prefixes(monkeypatch: pytest.MonkeyPatch) -> None:
    sys_message = SystemMessage(content="You are a helpful AI agent, and you answer questions in a friendly way.")
    assistant_message = AssistantMessage(content="Hello, how can I help you?", source="Assistant")
    user_text_message = UserMessage(content="Hello, I am from Seattle.", source="Adam")
    user_mm_message = UserMessage(
        content=[
            "Here is a postcard from Seattle:",
            Image.from_base64(
                "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAIAAACQd1PeAAAADElEQVR4nGP4z8AAAAMBAQDJ/pLvAAAAAElFTkSuQmCC"
            ),
        ],
        source="Adam",
    )

    # Default conversion
    oai_sys = to_oai_type(sys_message)[0]
    oai_asst = to_oai_type(assistant_message)[0]
    oai_text = to_oai_type(user_text_message)[0]
    oai_mm = to_oai_type(user_mm_message)[0]

    converted_sys = to_oai_type(sys_message, prepend_name=True)[0]
    converted_asst = to_oai_type(assistant_message, prepend_name=True)[0]
    converted_text = to_oai_type(user_text_message, prepend_name=True)[0]
    converted_mm = to_oai_type(user_mm_message, prepend_name=True)[0]

    # Invariants
    assert "content" in oai_sys
    assert "content" in oai_asst
    assert "content" in oai_text
    assert "content" in oai_mm
    assert "content" in converted_sys
    assert "content" in converted_asst
    assert "content" in converted_text
    assert "content" in converted_mm
    assert oai_sys["role"] == converted_sys["role"]
    assert oai_sys["content"] == converted_sys["content"]
    assert oai_asst["role"] == converted_asst["role"]
    assert oai_asst["content"] == converted_asst["content"]
    assert oai_text["role"] == converted_text["role"]
    assert oai_mm["role"] == converted_mm["role"]
    assert isinstance(oai_mm["content"], list)
    assert isinstance(converted_mm["content"], list)
    assert len(oai_mm["content"]) == len(converted_mm["content"])
    assert "text" in converted_mm["content"][0]
    assert "text" in oai_mm["content"][0]

    # Name prepended
    assert str(converted_text["content"]) == "Adam said:\n" + str(oai_text["content"])
    assert str(converted_mm["content"][0]["text"]) == "Adam said:\n" + str(oai_mm["content"][0]["text"])