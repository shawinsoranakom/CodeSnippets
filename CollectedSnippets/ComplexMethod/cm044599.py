def test_decode_newlines():
    """Test newlines are preserved.
    Regression test for https://github.com/Textualize/rich/issues/3577
    """
    assert Text.from_ansi("").plain == ""
    assert Text.from_ansi("\n").plain == "\n"
    assert Text.from_ansi("\n\n").plain == "\n\n"
    assert Text.from_ansi("Hello").plain == "Hello"
    assert Text.from_ansi("\nHello").plain == "\nHello"
    assert Text.from_ansi("Hello\n").plain == "Hello\n"
    assert Text.from_ansi("Hello\n\n").plain == "Hello\n\n"
    assert Text.from_ansi("Hello\nWorld").plain == "Hello\nWorld"
    assert Text.from_ansi("Hello\n\nWorld").plain == "Hello\n\nWorld"
    assert Text.from_ansi("Hello\nWorld\n").plain == "Hello\nWorld\n"
    assert Text.from_ansi("Hello\nWorld\n\n").plain == "Hello\nWorld\n\n"
    assert Text.from_ansi("\nHello\nWorld\n\n").plain == "\nHello\nWorld\n\n"