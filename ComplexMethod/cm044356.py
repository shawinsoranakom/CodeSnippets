def test__state__get_state_file(state_instance: _State,
                                mocker: pytest_mock.MockerFixture,
                                monkeypatch: pytest.MonkeyPatch) -> None:
    """ Test _get_state_file function for :class:`~lib.utils.sysinfo._State` """
    assert hasattr(state_instance, "_get_state_file")
    assert isinstance(state_instance._get_state_file(), str)

    mock_is_training = mocker.patch("lib.system.sysinfo._State._is_training")

    # Not training or missing training arguments
    mock_is_training.return_value = False
    assert state_instance._get_state_file() == ""
    mock_is_training.return_value = False

    monkeypatch.setattr(state_instance, "_model_dir", None)
    assert state_instance._get_state_file() == ""
    monkeypatch.setattr(state_instance, "_model_dir", "test_dir")

    monkeypatch.setattr(state_instance, "_trainer", None)
    assert state_instance._get_state_file() == ""
    monkeypatch.setattr(state_instance, "_trainer", "test_trainer")

    # Training but file not found
    assert state_instance._get_state_file() == ""

    # State file is just a json dump
    file = ('{\n'
            '   "test": "json",\n'
            '}')
    monkeypatch.setattr("os.path.isfile", lambda *args, **kwargs: True)
    monkeypatch.setattr("builtins.open", lambda *args, **kwargs: StringIO(file))
    assert state_instance._get_state_file().endswith(file)