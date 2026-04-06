def test_no_editor(mocker, monkeypatch, test):
    mocker.patch('os.path.isfile', return_value=True)
    if 'EDITOR' in os.environ:
        monkeypatch.delenv('EDITOR')

    assert not match(Command('', test.output))