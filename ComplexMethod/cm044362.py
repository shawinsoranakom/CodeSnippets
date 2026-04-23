def testConfigFile_sync_to_app(ini_config, app_config, status, mocker):
    """ Test :class:`lib.config.ini.ConfigFile._sync_to_app` logic """

    for sect in app_config.values():  # Add a dummy datatype param to FSConfig
        for opt in sect.options.values():
            setattr(opt, "datatype", str)

    instance = ini_mod.ConfigFile("test")
    instance._get_converted_value = mocker.MagicMock(return_value="updated_value")

    for section, opts in ini_config.items():  # Load up the dummy ini info
        instance._parser.add_section(section)
        for name, opt in opts.items():
            instance._parser[section][name] = opt

    instance._sync_to_app(app_config)

    app_values = {sname: set(v.value for v in sect.options.values())
                  for sname, sect in app_config.items()}
    sect_values = {sname: set(instance._parser[sname].values())
                   for sname in instance._parser.sections()}

    if status == "synced":  # No items change
        instance._get_converted_value.assert_not_called()
    else:  # 2 items updated in the config.ini
        assert instance._get_converted_value.call_count == 2

    # App and ini values must now match
    assert set(app_values) == set(sect_values)
    for sect in app_values:
        assert set(app_values[sect]) == set(sect_values[sect])