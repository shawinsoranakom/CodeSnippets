def test_match(mocker, monkeypatch, test):
    mocker.patch('os.path.isfile', return_value=True)
    monkeypatch.setenv('EDITOR', 'dummy_editor')
    assert match(Command('', test.output))