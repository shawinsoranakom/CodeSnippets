def test_markup_and_highlight():
    console = Console(
        file=io.StringIO(),
        force_terminal=True,
        width=140,
        color_system="truecolor",
        _environ={},
    )
    handler = RichHandler(console=console)

    # Check defaults are as expected
    assert handler.highlighter
    assert not handler.markup

    formatter = logging.Formatter("FORMATTER %(message)s %(asctime)s")
    handler.setFormatter(formatter)
    log.addHandler(handler)

    log_message = "foo 3.141 127.0.0.1 [red]alert[/red]"

    log.error(log_message)
    render_fancy = handler.console.file.getvalue()
    assert "FORMATTER" in render_fancy
    assert log_message not in render_fancy
    assert "red" in render_fancy

    handler.console.file = io.StringIO()
    log.error(log_message, extra={"markup": True})
    render_markup = handler.console.file.getvalue()
    assert "FORMATTER" in render_markup
    assert log_message not in render_markup
    assert "red" not in render_markup

    handler.console.file = io.StringIO()
    log.error(log_message, extra={"highlighter": None})
    render_plain = handler.console.file.getvalue()
    assert "FORMATTER" in render_plain
    assert log_message in render_plain