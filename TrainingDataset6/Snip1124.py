def test_match():
    assert match(Command('docker pes', output('pes')))