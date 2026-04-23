def test_highlight_words():
    text = Text("Do NOT! touch anything!")
    words = ["NOT", "!"]
    count = text.highlight_words(words, "red")
    assert count == 3
    assert sorted(text._spans) == [
        Span(3, 6, "red"),  # NOT
        Span(6, 7, "red"),  # !
        Span(22, 23, "red"),  # !
    ]

    # regex escape test
    text = Text("[o|u]aeiou")
    words = ["[a|e|i]", "[o|u]"]
    count = text.highlight_words(words, "red")
    assert count == 1
    assert text._spans == [Span(0, 5, "red")]

    # case sensitive
    text = Text("AB Ab aB ab")
    words = ["AB"]

    count = text.highlight_words(words, "red")
    assert count == 1
    assert text._spans == [Span(0, 2, "red")]

    text = Text("AB Ab aB ab")
    count = text.highlight_words(words, "red", case_sensitive=False)
    assert count == 4