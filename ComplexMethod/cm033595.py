def test_install_collection_with_download(galaxy_server, collection_artifact, monkeypatch):
    collection_path, collection_tar = collection_artifact
    shutil.rmtree(collection_path)

    collections_dir = ('%s' % os.path.sep).join(to_text(collection_path).split('%s' % os.path.sep)[:-2])

    temp_path = os.path.join(os.path.split(collection_tar)[0], b'temp')
    os.makedirs(temp_path)

    mock_display = MagicMock()
    monkeypatch.setattr(Display, 'display', mock_display)

    concrete_artifact_cm = collection.concrete_artifact_manager.ConcreteArtifactsManager(temp_path, validate_certs=False)

    mock_download = MagicMock()
    mock_download.return_value = collection_tar
    monkeypatch.setattr(concrete_artifact_cm, 'get_galaxy_artifact_path', mock_download)

    req = Candidate('ansible_namespace.collection', '0.1.0', 'https://downloadme.com', 'galaxy', None)
    collection.install(req, to_text(collections_dir), concrete_artifact_cm)

    actual_files = os.listdir(collection_path)
    actual_files.sort()
    assert actual_files == [b'FILES.json', b'MANIFEST.json', b'README.md', b'docs', b'playbooks', b'plugins', b'roles',
                            b'runme.sh']

    assert mock_display.call_count == 2
    assert mock_display.mock_calls[0][1][0] == "Installing 'ansible_namespace.collection:0.1.0' to '%s'" \
        % to_text(collection_path)
    assert mock_display.mock_calls[1][1][0] == "ansible_namespace.collection:0.1.0 was installed successfully"

    assert mock_download.call_count == 1
    assert mock_download.mock_calls[0][1][0].src == 'https://downloadme.com'
    assert mock_download.mock_calls[0][1][0].type == 'galaxy'