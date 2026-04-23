def test_collection_install_in_collection_dir(collection_install, monkeypatch):
    mock_install, mock_warning, output_dir = collection_install

    collections_path = C.COLLECTIONS_PATHS[0]

    galaxy_args = ['ansible-galaxy', 'collection', 'install', 'namespace.collection', 'namespace2.collection:1.0.1',
                   '--collections-path', collections_path]
    GalaxyCLI(args=galaxy_args).run()

    assert mock_warning.call_count == 0

    assert mock_install.call_count == 1
    requirements = [('%s.%s' % (r.namespace, r.name), r.ver, r.src, r.type,) for r in mock_install.call_args[0][0]]
    assert requirements == [('namespace.collection', '*', None, 'galaxy'),
                            ('namespace2.collection', '1.0.1', None, 'galaxy')]
    assert mock_install.call_args[0][1] == os.path.join(collections_path, 'ansible_collections')
    assert len(mock_install.call_args[0][2]) == 1
    assert mock_install.call_args[0][2][0].api_server == 'https://galaxy.ansible.com'
    assert mock_install.call_args[0][2][0].validate_certs is True
    assert mock_install.call_args[0][3] is False  # ignore_errors
    assert mock_install.call_args[0][4] is False  # no_deps
    assert mock_install.call_args[0][5] is False  # force
    assert mock_install.call_args[0][6] is False