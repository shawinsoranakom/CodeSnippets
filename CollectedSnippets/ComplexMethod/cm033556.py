def test_install_implicit_role_with_collections(requirements_file, monkeypatch):
    mock_collection_install = MagicMock()
    monkeypatch.setattr(GalaxyCLI, '_execute_install_collection', mock_collection_install)
    mock_role_install = MagicMock()
    monkeypatch.setattr(GalaxyCLI, '_execute_install_role', mock_role_install)

    mock_display = MagicMock()
    monkeypatch.setattr(Display, 'display', mock_display)

    cli = GalaxyCLI(args=['ansible-galaxy', 'install', '-r', requirements_file])
    cli.run()

    assert mock_collection_install.call_count == 1
    requirements = [('%s.%s' % (r.namespace, r.name), r.ver, r.src, r.type,) for r in mock_collection_install.call_args[0][0]]
    assert requirements == [('namespace.name', '*', None, 'galaxy')]
    assert mock_collection_install.call_args[0][1] == cli._get_default_collection_path()

    assert mock_role_install.call_count == 1
    assert len(mock_role_install.call_args[0][0]) == 1
    assert str(mock_role_install.call_args[0][0][0]) == 'namespace.name'

    assert not any(list('contains collections which will be ignored' in mock_call[1][0] for mock_call in mock_display.mock_calls))