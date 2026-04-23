def test_numbered_list() -> None:
    parser = NumberedListOutputParser()
    text1 = (
        "Your response should be a numbered list with each item on a new line. "
        "For example: \n\n1. foo\n\n2. bar\n\n3. baz"
    )

    text2 = "Items:\n\n1. apple\n\n    2. banana\n\n3. cherry"

    text3 = "No items in the list."

    for text, expected in [
        (text1, ["foo", "bar", "baz"]),
        (text2, ["apple", "banana", "cherry"]),
        (text3, []),
    ]:
        expectedlist = [[a] for a in expected]
        assert parser.parse(text) == expected
        assert add(parser.transform(t for t in text)) == (expected or None)
        assert list(parser.transform(t for t in text)) == expectedlist
        assert (
            list(parser.transform(t for t in text.splitlines(keepends=True)))
            == expectedlist
        )
        assert (
            list(
                parser.transform(
                    " " + t if i > 0 else t for i, t in enumerate(text.split(" "))
                )
            )
            == expectedlist
        )
        assert list(parser.transform(iter([text]))) == expectedlist