def test_collection_install_with_url(monkeypatch, collection_install):
    mock_install, dummy, output_dir = collection_install

    mock_open = MagicMock(return_value=BytesIO())
    monkeypatch.setattr(collection.concrete_artifact_manager, 'open_url', mock_open)

    mock_metadata = MagicMock(return_value={'namespace': 'foo', 'name': 'bar', 'version': 'v1.0.0'})
    monkeypatch.setattr(collection.concrete_artifact_manager, '_get_meta_from_tar', mock_metadata)

    galaxy_args = ['ansible-galaxy', 'collection', 'install', 'https://foo/bar/foo-bar-v1.0.0.tar.gz',
                   '--collections-path', output_dir]
    GalaxyCLI(args=galaxy_args).run()

    collection_path = os.path.join(output_dir, 'ansible_collections')
    assert os.path.isdir(collection_path)

    assert mock_install.call_count == 1
    requirements = [('%s.%s' % (r.namespace, r.name), r.ver, r.src, r.type,) for r in mock_install.call_args[0][0]]
    assert requirements == [('foo.bar', 'v1.0.0', 'https://foo/bar/foo-bar-v1.0.0.tar.gz', 'url')]
    assert mock_install.call_args[0][1] == collection_path
    assert len(mock_install.call_args[0][2]) == 1
    assert mock_install.call_args[0][2][0].api_server == 'https://galaxy.ansible.com'
    assert mock_install.call_args[0][2][0].validate_certs is True
    assert mock_install.call_args[0][3] is False  # ignore_errors
    assert mock_install.call_args[0][4] is False  # no_deps
    assert mock_install.call_args[0][5] is False  # force
    assert mock_install.call_args[0][6] is False