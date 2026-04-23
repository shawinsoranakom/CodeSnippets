def test_highlight_regex():
    # As a string
    text = Text("peek-a-boo")

    count = text.highlight_regex(r"NEVER_MATCH", "red")
    assert count == 0
    assert len(text._spans) == 0

    # text: peek-a-boo
    # indx: 0123456789
    count = text.highlight_regex(r"[a|e|o]+", "red")
    assert count == 3
    assert sorted(text._spans) == [
        Span(1, 3, "red"),
        Span(5, 6, "red"),
        Span(8, 10, "red"),
    ]

    text = Text("Ada Lovelace, Alan Turing")

    count = text.highlight_regex(
        r"(?P<yellow>[A-Za-z]+)[ ]+(?P<red>[A-Za-z]+)(?P<NEVER_MATCH>NEVER_MATCH)*"
    )

    # The number of matched name should be 2
    assert count == 2
    assert sorted(text._spans) == [
        Span(0, 3, "yellow"),  # Ada
        Span(4, 12, "red"),  # Lovelace
        Span(14, 18, "yellow"),  # Alan
        Span(19, 25, "red"),  # Turing
    ]

    # As a regular expression object
    text = Text("peek-a-boo")

    count = text.highlight_regex(re.compile(r"NEVER_MATCH"), "red")
    assert count == 0
    assert len(text._spans) == 0

    # text: peek-a-boo
    # indx: 0123456789
    count = text.highlight_regex(re.compile(r"[a|e|o]+"), "red")
    assert count == 3
    assert sorted(text._spans) == [
        Span(1, 3, "red"),
        Span(5, 6, "red"),
        Span(8, 10, "red"),
    ]

    text = Text("Ada Lovelace, Alan Turing")

    count = text.highlight_regex(
        re.compile(
            r"(?P<yellow>[A-Za-z]+)[ ]+(?P<red>[A-Za-z]+)(?P<NEVER_MATCH>NEVER_MATCH)*"
        )
    )

    # The number of matched name should be 2
    assert count == 2
    assert sorted(text._spans) == [
        Span(0, 3, "yellow"),  # Ada
        Span(4, 12, "red"),  # Lovelace
        Span(14, 18, "yellow"),  # Alan
        Span(19, 25, "red"),  # Turing
    ]