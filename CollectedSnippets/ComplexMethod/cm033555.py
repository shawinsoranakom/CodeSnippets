def test_parse_requirements_with_collection_source(requirements_cli, requirements_file):
    galaxy_api = GalaxyAPI(requirements_cli.api, 'server', 'https://config-server')
    requirements_cli.api_servers.append(galaxy_api)

    actual = requirements_cli._parse_requirements_file(requirements_file)
    actual['collections'] = [('%s.%s' % (r.namespace, r.name), r.ver, r.src, r.type,) for r in actual.get('collections', [])]

    assert actual['roles'] == []
    assert len(actual['collections']) == 3
    assert actual['collections'][0] == ('namespace.collection', '*', None, 'galaxy')

    assert actual['collections'][1][0] == 'namespace2.collection2'
    assert actual['collections'][1][1] == '*'
    assert actual['collections'][1][2].api_server == 'https://galaxy-dev.ansible.com/'

    assert actual['collections'][2][0] == 'namespace3.collection3'
    assert actual['collections'][2][1] == '*'
    assert actual['collections'][2][2].api_server == 'https://config-server'