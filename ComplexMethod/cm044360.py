def test_ConfigFile_is_synced_structure():
    """ Test that :class:`lib.config.ini.ConfigFile.is_synced_structure` is logical """
    instance = ini_mod.ConfigFile("test")

    sect_sizes = [2, 1, 3]
    parser_sects, fs_sects = get_local_remote(sect_sizes)

    # No Config
    test = instance._is_synced_structure(fs_sects)
    assert test is False

    # Sects exist
    for section in parser_sects:
        instance._parser.add_section(section)

    test = instance._is_synced_structure(fs_sects)
    assert test is False

    # Some Options missing
    for section, options in parser_sects.items():
        for opt, val in options.items():
            instance._parser.set(section, opt, val)
            break

    test = instance._is_synced_structure(fs_sects)
    assert test is False

    # Structure matches
    for section, options in parser_sects.items():
        for opt, val in options.items():
            instance._parser.set(section, opt, val)

    test = instance._is_synced_structure(fs_sects)
    assert test is True

    # Extra saved section
    instance._parser.add_section("text_extra_section")
    test = instance._is_synced_structure(fs_sects)
    assert test is False

    # Structure matches
    del instance._parser["text_extra_section"]
    test = instance._is_synced_structure(fs_sects)
    assert test is True

    # Extra Option
    instance._parser.set(section, "opt_test_extra_option", "val_test_extra_option")
    test = instance._is_synced_structure(fs_sects)
    assert test is False