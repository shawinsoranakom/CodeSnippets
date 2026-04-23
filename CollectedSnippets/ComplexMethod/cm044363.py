def testConfigFile_sync_update_from_app(app_config, mocker):
    """ Test :class:`lib.config.ini.ConfigFile.update_from_app` logic """
    instance = ini_mod.ConfigFile("test")
    instance.save = mocker.MagicMock()
    for sect in app_config:
        # Updating from app always replaces the existing parser with a new one
        assert sect not in instance._parser.sections()

    instance.update_from_app(app_config)

    instance.save.assert_called_once()
    for sect_name, sect in app_config.items():
        assert sect_name in instance._parser.sections()
        for opt_name, val in sect.options.items():
            assert opt_name in instance._parser[sect_name]
            assert instance._parser[sect_name][opt_name] == val.ini_value