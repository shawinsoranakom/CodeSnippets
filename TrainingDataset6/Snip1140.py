def test_not_file(mocker, monkeypatch, test):
    mocker.patch('os.path.isfile', return_value=False)
    monkeypatch.setenv('EDITOR', 'dummy_editor')

    assert not match(Command('', test.output))