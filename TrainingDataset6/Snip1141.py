def test_get_new_command(mocker, monkeypatch, test):
    mocker.patch('os.path.isfile', return_value=True)
    monkeypatch.setenv('EDITOR', 'dummy_editor')