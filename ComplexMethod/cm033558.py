def test_execute_list_collection_specific_duplicate(mocker, capsys, mock_from_path, tmp_path_factory):
    """Test listing a specific collection that exists at multiple paths"""

    collection_name = 'sandwiches.pbj'

    cliargs(collection_name=collection_name)

    mocker.patch('ansible.galaxy.collection.validate_collection_name', collection_name)

    gc = GalaxyCLI(['ansible-galaxy', 'collection', 'list', collection_name])
    tmp_path = tmp_path_factory.mktemp('test-ÅÑŚÌβŁÈ Collections')
    concrete_artifact_cm = collection.concrete_artifact_manager.ConcreteArtifactsManager(tmp_path, validate_certs=False)
    gc.execute_list_collection(artifacts_manager=concrete_artifact_cm)

    out, err = capsys.readouterr()
    out_lines = out.splitlines()

    assert len(out_lines) == 10
    assert out_lines[0] == ''
    assert out_lines[1] == '# /root/.ansible/collections/ansible_collections'
    assert out_lines[2] == 'Collection     Version'
    assert out_lines[3] == '-------------- -------'
    assert out_lines[4] == 'sandwiches.pbj 1.5.0  '
    assert out_lines[5] == ''
    assert out_lines[6] == '# /usr/share/ansible/collections/ansible_collections'
    assert out_lines[7] == 'Collection     Version'
    assert out_lines[8] == '-------------- -------'
    assert out_lines[9] == 'sandwiches.pbj 1.0.0  '