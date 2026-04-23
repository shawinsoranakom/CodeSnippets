def test_match():
    assert match(Command('systemctl nginx start', 'Unknown operation \'nginx\'.'))
    assert match(Command('sudo systemctl nginx start', 'Unknown operation \'nginx\'.'))
    assert not match(Command('systemctl start nginx', ''))
    assert not match(Command('systemctl start nginx', ''))
    assert not match(Command('sudo systemctl nginx', 'Unknown operation \'nginx\'.'))
    assert not match(Command('systemctl nginx', 'Unknown operation \'nginx\'.'))
    assert not match(Command('systemctl start wtf', 'Failed to start wtf.service: Unit wtf.service failed to load: No such file or directory.'))