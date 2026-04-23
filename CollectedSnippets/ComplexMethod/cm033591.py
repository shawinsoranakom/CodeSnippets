def test_build_requirement_from_name_single_version(galaxy_server, monkeypatch, tmp_path_factory):
    test_dir = to_bytes(tmp_path_factory.mktemp('test-ÅÑŚÌβŁÈ Collections Input'))
    concrete_artifact_cm = collection.concrete_artifact_manager.ConcreteArtifactsManager(test_dir, validate_certs=False)
    multi_api_proxy = collection.galaxy_api_proxy.MultiGalaxyAPIProxy([galaxy_server], concrete_artifact_cm)
    dep_provider = dependency_resolution.providers.CollectionDependencyProvider(apis=multi_api_proxy, concrete_artifacts_manager=concrete_artifact_cm)

    matches = RequirementCandidates()
    mock_find_matches = MagicMock(side_effect=matches.func_wrapper(dep_provider.find_matches), autospec=True)
    monkeypatch.setattr(dependency_resolution.providers.CollectionDependencyProvider, 'find_matches', mock_find_matches)

    mock_get_versions = MagicMock()
    mock_get_versions.return_value = ['2.0.0']
    monkeypatch.setattr(galaxy_server, 'get_collection_versions', mock_get_versions)

    mock_get_info = MagicMock()
    mock_get_info.return_value = api.CollectionVersionMetadata('namespace', 'collection', '2.0.0', None, None,
                                                               {}, None, None)
    monkeypatch.setattr(galaxy_server, 'get_collection_version_metadata', mock_get_info)

    cli = GalaxyCLI(args=['ansible-galaxy', 'collection', 'install', 'namespace.collection:==2.0.0'])
    requirements = cli._require_one_of_collections_requirements(
        ['namespace.collection:==2.0.0'], None, artifacts_manager=concrete_artifact_cm
    )['collections']

    actual = collection._resolve_depenency_map(
        requirements, [galaxy_server], concrete_artifact_cm, None, False, True, False, False, False)['namespace.collection']

    assert actual.namespace == u'namespace'
    assert actual.name == u'collection'
    assert actual.src == galaxy_server
    assert actual.ver == u'2.0.0'
    assert [c.ver for c in matches.candidates] == [u'2.0.0']

    assert mock_get_info.call_count == 1
    assert mock_get_info.mock_calls[0][1] == ('namespace', 'collection', '2.0.0')