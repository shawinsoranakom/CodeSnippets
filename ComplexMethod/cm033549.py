def test_collection_install_with_unexpanded_path(collection_install, monkeypatch):
    mock_install = collection_install[0]

    mock_req = MagicMock()
    mock_req.return_value = {'collections': [('namespace.coll', '*', None, None)], 'roles': []}
    monkeypatch.setattr(ansible.cli.galaxy.GalaxyCLI, '_parse_requirements_file', mock_req)

    monkeypatch.setattr(os, 'makedirs', MagicMock())

    requirements_file = '~/requirements.myl'
    collections_path = '~/ansible_collections'
    galaxy_args = ['ansible-galaxy', 'collection', 'install', '--requirements-file', requirements_file,
                   '--collections-path', collections_path]
    GalaxyCLI(args=galaxy_args).run()

    assert mock_install.call_count == 1
    assert mock_install.call_args[0][0] == [('namespace.coll', '*', None, None)]
    assert mock_install.call_args[0][1] == os.path.expanduser(os.path.expandvars(collections_path))
    assert len(mock_install.call_args[0][2]) == 1
    assert mock_install.call_args[0][2][0].api_server == 'https://galaxy.ansible.com'
    assert mock_install.call_args[0][2][0].validate_certs is True
    assert mock_install.call_args[0][3] is False  # ignore_errors
    assert mock_install.call_args[0][4] is False  # no_deps
    assert mock_install.call_args[0][5] is False  # force
    assert mock_install.call_args[0][6] is False  # force_deps

    assert mock_req.call_count == 1
    assert mock_req.call_args[0][0] == os.path.expanduser(os.path.expandvars(requirements_file))