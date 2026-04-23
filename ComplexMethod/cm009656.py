def test_message_text() -> None:
    # partitions:
    # message types: [ai], [human], [system], [tool]
    # content types: [str], [list[str]], [list[dict]], [list[str | dict]]
    # content: [empty], [single element], [multiple elements]
    # content dict types: [text], [not text], [no type]

    assert HumanMessage(content="foo").text == "foo"
    assert AIMessage(content=[]).text == ""
    assert AIMessage(content=["foo", "bar"]).text == "foobar"
    assert (
        AIMessage(
            content=[
                {"type": "text", "text": "<thinking>thinking...</thinking>"},
                {
                    "type": "tool_use",
                    "id": "toolu_01A09q90qw90lq917835lq9",
                    "name": "get_weather",
                    "input": {"location": "San Francisco, CA"},
                },
            ]
        ).text
        == "<thinking>thinking...</thinking>"
    )
    assert (
        SystemMessage(content=[{"type": "text", "text": "foo"}, "bar"]).text == "foobar"
    )
    assert (
        ToolMessage(
            content=[
                {"type": "text", "text": "15 degrees"},
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/jpeg",
                        "data": "/9j/4AAQSkZJRg...",
                    },
                },
            ],
            tool_call_id="1",
        ).text
        == "15 degrees"
    )
    assert (
        AIMessage(content=[{"text": "hi there"}, "hi"]).text == "hi"
    )  # missing type: text
    assert AIMessage(content=[{"type": "nottext", "text": "hi"}]).text == ""
    assert AIMessage(content=[]).text == ""
    assert (
        AIMessage(
            content="", tool_calls=[create_tool_call(name="a", args={"b": 1}, id=None)]
        ).text
        == ""
    )