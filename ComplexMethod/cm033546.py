def test_collection_install_with_names(collection_install):
    mock_install, mock_warning, output_dir = collection_install

    galaxy_args = ['ansible-galaxy', 'collection', 'install', 'namespace.collection', 'namespace2.collection:1.0.1',
                   '--collections-path', output_dir]
    GalaxyCLI(args=galaxy_args).run()

    collection_path = os.path.join(output_dir, 'ansible_collections')
    assert os.path.isdir(collection_path)

    assert mock_warning.call_count == 1
    assert "The specified collections path '%s' is not part of the configured Ansible collections path" % output_dir \
        in mock_warning.call_args[0][0]

    assert mock_install.call_count == 1
    requirements = [('%s.%s' % (r.namespace, r.name), r.ver, r.src, r.type,) for r in mock_install.call_args[0][0]]
    assert requirements == [('namespace.collection', '*', None, 'galaxy'),
                            ('namespace2.collection', '1.0.1', None, 'galaxy')]
    assert mock_install.call_args[0][1] == collection_path
    assert len(mock_install.call_args[0][2]) == 1
    assert mock_install.call_args[0][2][0].api_server == 'https://galaxy.ansible.com'
    assert mock_install.call_args[0][2][0].validate_certs is True
    assert mock_install.call_args[0][3] is False  # ignore_errors
    assert mock_install.call_args[0][4] is False  # no_deps
    assert mock_install.call_args[0][5] is False  # force
    assert mock_install.call_args[0][6] is False