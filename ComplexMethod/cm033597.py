def test_install_collection_with_circular_dependency(collection_artifact, monkeypatch):
    collection_path, collection_tar = collection_artifact
    temp_path = os.path.split(collection_tar)[0]
    shutil.rmtree(collection_path)

    mock_display = MagicMock()
    monkeypatch.setattr(Display, 'display', mock_display)

    concrete_artifact_cm = collection.concrete_artifact_manager.ConcreteArtifactsManager(temp_path, validate_certs=False)
    requirements = [Requirement('ansible_namespace.collection', '0.1.0', to_text(collection_tar), 'file', None)]
    collection.install_collections(
        requirements, to_text(temp_path), [], False, False, False, False, False, False, concrete_artifact_cm, True, False, set())

    assert os.path.isdir(collection_path)

    actual_files = os.listdir(collection_path)
    actual_files.sort()
    assert actual_files == [b'FILES.json', b'MANIFEST.json', b'README.md', b'docs', b'playbooks', b'plugins', b'roles',
                            b'runme.sh']

    with open(os.path.join(collection_path, b'MANIFEST.json'), 'rb') as manifest_obj:
        actual_manifest = json.loads(to_text(manifest_obj.read()))

    assert actual_manifest['collection_info']['namespace'] == 'ansible_namespace'
    assert actual_manifest['collection_info']['name'] == 'collection'
    assert actual_manifest['collection_info']['version'] == '0.1.0'
    assert actual_manifest['collection_info']['dependencies'] == {'ansible_namespace.collection': '>=0.0.1'}

    # Filter out the progress cursor display calls.
    display_msgs = [m[1][0] for m in mock_display.mock_calls if 'newline' not in m[2] and len(m[1]) == 1]
    assert len(display_msgs) == 5
    assert display_msgs[0] == "Process install dependency map"
    assert display_msgs[1] == "[WARNING]: ansible_namespace.collection:0.1.0 does not have requires_ansible metadata.\n"
    assert display_msgs[2] == "Starting collection install process"
    assert display_msgs[3] == "Installing 'ansible_namespace.collection:0.1.0' to '%s'" % to_text(collection_path)
    assert display_msgs[4] == "ansible_namespace.collection:0.1.0 was installed successfully"