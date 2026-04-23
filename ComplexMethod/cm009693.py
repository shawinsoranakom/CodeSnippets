async def test_markdown_list_async() -> None:
    parser = MarkdownListOutputParser()
    text1 = (
        "Your response should be a numbered list with each item on a new line."
        "For example: \n- foo\n- bar\n- baz"
    )

    text2 = "Items:\n- apple\n- banana\n- cherry"

    text3 = "No items in the list."

    for text, expected in [
        (text1, ["foo", "bar", "baz"]),
        (text2, ["apple", "banana", "cherry"]),
        (text3, []),
    ]:
        expectedlist = [[a] for a in expected]
        assert await parser.aparse(text) == expected
        assert await aadd(parser.atransform(aiter_from_iter(t for t in text))) == (
            expected or None
        )
        assert [
            a async for a in parser.atransform(aiter_from_iter(t for t in text))
        ] == expectedlist
        assert [
            a
            async for a in parser.atransform(
                aiter_from_iter(t for t in text.splitlines(keepends=True))
            )
        ] == expectedlist
        assert [
            a
            async for a in parser.atransform(
                aiter_from_iter(
                    " " + t if i > 0 else t for i, t in enumerate(text.split(" "))
                )
            )
        ] == expectedlist
        assert [
            a async for a in parser.atransform(aiter_from_iter([text]))
        ] == expectedlist