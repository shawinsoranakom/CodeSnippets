def test_get_user_dir_path(mocker, os_environ, settings, legacy_dir_exists,
                           xdg_config_home, result):
    mocker.patch('thefuck.conf.Path.is_dir',
                 return_value=legacy_dir_exists)

    if xdg_config_home is not None:
        os_environ['XDG_CONFIG_HOME'] = xdg_config_home
    else:
        os_environ.pop('XDG_CONFIG_HOME', None)

    path = settings._get_user_dir_path().as_posix()
    assert path == os.path.expanduser(result)