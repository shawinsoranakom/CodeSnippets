def test_from_ansi():
    text = Text.from_ansi("Hello, \033[1mWorld!\033[0m")
    assert str(text) == "Hello, World!"
    assert text._spans == [Span(7, 13, Style(bold=True))]

    text = Text.from_ansi("Hello, \033[1m\nWorld!\033[0m")
    assert str(text) == "Hello, \nWorld!"
    assert text._spans == [Span(8, 14, Style(bold=True))]

    text = Text.from_ansi("\033[1mBOLD\033[m not bold")
    assert str(text) == "BOLD not bold"
    assert text._spans == [Span(0, 4, Style(bold=True))]

    text = Text.from_ansi("\033[1m\033[Kfoo barmbaz")
    assert str(text) == "foo barmbaz"
    assert text._spans == [Span(0, 11, Style(bold=True))]