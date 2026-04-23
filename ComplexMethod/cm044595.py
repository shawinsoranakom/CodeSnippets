def test_tty_compatible() -> None:
    """Check TTY_COMPATIBLE environment var."""

    class FakeTTY:
        """An file file-like which reports it is a TTY."""

        def __init__(self) -> None:
            self.called_isatty = False

        def isatty(self) -> bool:
            self.called_isatty = True
            return True

    class FakeFile:
        """A file object that reports False for isatty"""

        def __init__(self) -> None:
            self.called_isatty = False

        def isatty(self) -> bool:
            self.called_isatty = True
            return False

    # Console file is not a TTY
    console = Console(file=FakeFile())
    # Not a TTY, so is_terminal should be False
    assert not console.is_terminal
    # Should have called isatty to auto-detect tty support
    assert console.file.called_isatty

    # Not a terminal
    console = Console(file=FakeFile(), _environ={"TTY_COMPATIBLE": "1"})
    # env TTY_COMPATIBLE=1 should report that it is a terminal
    assert console.is_terminal
    # Should not have called file.isattry
    assert not console.file.called_isatty

    # File is a fake TTY
    console = Console(file=FakeTTY())
    # Should report True
    assert console.is_terminal
    # Should have auto-detected
    assert console.file.called_isatty

    # File is a fake TTY
    console = Console(file=FakeTTY(), _environ={"TTY_COMPATIBLE": ""})
    # Blank TTY_COMPATIBLE should auto-detect, so is_terminal is True
    assert console.is_terminal
    # Should have auto-detected
    assert console.file.called_isatty

    # File is a fake TTY
    console = Console(file=FakeTTY(), _environ={"TTY_COMPATIBLE": "whatever"})
    # Any pother value should auto-detect
    assert console.is_terminal
    # Should have auto-detected
    assert console.file.called_isatty

    # TTY_COMPATIBLE should override file.isattry
    console = Console(file=FakeTTY(), _environ={"TTY_COMPATIBLE": "0"})
    # Should report that it is *not* a terminal
    assert not console.is_terminal
    # Should not have auto-detected
    assert not console.file.called_isatty