def test_divide():
    lines = Text("foo").divide([])
    assert len(lines) == 1
    assert lines[0] == Text("foo")

    text = Text()
    text.append("foo", "bold")
    lines = text.divide([1, 2])
    assert len(lines) == 3
    assert str(lines[0]) == "f"
    assert str(lines[1]) == "o"
    assert str(lines[2]) == "o"
    assert lines[0]._spans == [Span(0, 1, "bold")]
    assert lines[1]._spans == [Span(0, 1, "bold")]
    assert lines[2]._spans == [Span(0, 1, "bold")]

    text = Text()
    text.append("foo", "red")
    text.append("bar", "green")
    text.append("baz", "blue")
    lines = text.divide([8])
    assert len(lines) == 2
    assert str(lines[0]) == "foobarba"
    assert str(lines[1]) == "z"
    assert lines[0]._spans == [
        Span(0, 3, "red"),
        Span(3, 6, "green"),
        Span(6, 8, "blue"),
    ]
    assert lines[1]._spans == [Span(0, 1, "blue")]

    lines = text.divide([1])
    assert len(lines) == 2
    assert str(lines[0]) == "f"
    assert str(lines[1]) == "oobarbaz"
    assert lines[0]._spans == [Span(0, 1, "red")]
    assert lines[1]._spans == [
        Span(0, 2, "red"),
        Span(2, 5, "green"),
        Span(5, 8, "blue"),
    ]