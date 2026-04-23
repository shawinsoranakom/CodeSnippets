def testConfigFile_sync_from_app(ini_config,  # pylint:disable=too-many-branches  # noqa[C901]
                                 app_config,
                                 status,
                                 exists,
                                 mocker):
    """ Test :class:`lib.config.ini.ConfigFile._sync_from_app` logic """
    mocker.patch("lib.config.ini.ConfigFile._exists", exists)

    instance = ini_mod.ConfigFile("test")
    instance.save = mocker.MagicMock()

    original_parser = instance._parser

    if exists:
        for section, opts in ini_config.items():
            original_parser.add_section(section)
            for name, opt in opts.items():
                original_parser[section][name] = opt

        opt_pairs = [({k: v.value for k, v in opts.options.items()},
                      dict(original_parser[s].items()))
                     for s, opts in app_config.items()]
        # Sanity check that the loaded parser is set correctly
        if status == "synced":
            assert all(set(x[0]) == set(x[1]) for x in opt_pairs)
        elif status == "new_from_app":
            assert any(len(x[1]) < len(x[0]) for x in opt_pairs)
        elif status == "new_from_ini":
            assert any(len(x[0]) < len(x[1]) for x in opt_pairs)
        elif status == "updated_ini":
            vals = [(set(x[0].values()), set(x[1].values())) for x in opt_pairs]
            assert not all(a == i for a, i in vals)
    else:
        for section in ini_config:
            assert section not in instance._parser

    instance._sync_from_app(app_config)  # Sync

    instance.save.assert_called_once()  # Saved
    if exists:
        assert instance._parser is not original_parser  # New config Generated
    else:
        assert instance._parser is original_parser  # Blank Config pre-exists

    opt_pairs = [({k: v.value for k, v in opts.options.items()},
                  {k: v for k, v in instance._parser[s].items() if k.startswith("opt")})
                 for s, opts in app_config.items()]

    # Test options are now in sync
    assert all(set(x[0]) == set(x[1]) for x in opt_pairs)
    # Test that ini value kept
    vals = [(set(x[0].values()), set(x[1].values())) for x in opt_pairs]
    if exists and status == "updated_ini":
        assert any("updated_value" in i for _, i in vals)
        assert any(a != i for a, i in vals)
    else:
        assert not any("updated_value" in i for _, i in vals)
        assert all(a == i for a, i in vals)