def test_match():
    assert match(Command('ls', ''))
    assert match(Command('ls file.py', ''))
    assert match(Command('ls /opt', ''))
    assert not match(Command('ls -lah /opt', ''))
    assert not match(Command('pacman -S binutils', ''))
    assert not match(Command('lsof', ''))