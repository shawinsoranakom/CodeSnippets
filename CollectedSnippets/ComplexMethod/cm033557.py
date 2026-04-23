def test_execute_list_collection_all(mocker, capsys, mock_from_path, tmp_path_factory):
    """Test listing all collections from multiple paths"""

    cliargs()

    mocker.patch('os.path.exists', return_value=True)
    gc = GalaxyCLI(['ansible-galaxy', 'collection', 'list'])
    tmp_path = tmp_path_factory.mktemp('test-ÅÑŚÌβŁÈ Collections')
    concrete_artifact_cm = collection.concrete_artifact_manager.ConcreteArtifactsManager(tmp_path, validate_certs=False)
    gc.execute_list_collection(artifacts_manager=concrete_artifact_cm)

    out, err = capsys.readouterr()
    out_lines = out.splitlines()

    assert len(out_lines) == 12
    assert out_lines[0] == ''
    assert out_lines[1] == '# /root/.ansible/collections/ansible_collections'
    assert out_lines[2] == 'Collection        Version'
    assert out_lines[3] == '----------------- -------'
    assert out_lines[4] == 'sandwiches.pbj    1.5.0  '
    assert out_lines[5] == 'sandwiches.reuben 2.5.0  '
    assert out_lines[6] == ''
    assert out_lines[7] == '# /usr/share/ansible/collections/ansible_collections'
    assert out_lines[8] == 'Collection        Version'
    assert out_lines[9] == '----------------- -------'
    assert out_lines[10] == 'sandwiches.ham    1.0.0  '
    assert out_lines[11] == 'sandwiches.pbj    1.0.0  '