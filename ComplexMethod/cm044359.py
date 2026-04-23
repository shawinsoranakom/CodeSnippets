def test_ConfigFile(tmpdir, mocker, plugin_group, config):
    """ Test that :class:`lib.config.ini.ConfigFile` initializes correctly """
    root_conf = tmpdir.mkdir("root").mkdir("config").join(f"{plugin_group}.ini")
    root_dir = os.path.dirname(os.path.dirname(root_conf))
    if config != "root_missing":
        root_conf.write("")
    mocker.patch("lib.config.ini.PROJECT_ROOT", root_dir)

    conf_file = None
    if config.startswith("custom"):
        conf_file = tmpdir.mkdir("config").join("test_custom_config.ini")
        if config == "custom":
            conf_file.write("")

    mock_load = mocker.MagicMock()
    mocker.patch("lib.config.ini.ConfigFile.load", mock_load)

    if config == "custom_missing":  # Error on explicit missing
        with pytest.raises(ValueError):
            ini_mod.ConfigFile("group2test", conf_file)
        return

    instance = ini_mod.ConfigFile(plugin_group, conf_file)
    file_path = conf_file if config == "custom" else root_conf
    assert instance._file_path == file_path
    assert instance._plugin_group == plugin_group
    assert instance._parser.optionxform is str

    if config in ("custom", "root"):  # load when exists
        mock_load.assert_called_once()
    else:
        mock_load.assert_not_called()