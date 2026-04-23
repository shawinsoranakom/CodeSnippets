def test_parse_requirements_with_extra_info(requirements_cli, requirements_file):
    actual = requirements_cli._parse_requirements_file(requirements_file)
    actual['collections'] = [('%s.%s' % (r.namespace, r.name), r.ver, r.src, r.type,) for r in actual.get('collections', [])]

    assert len(actual['roles']) == 0
    assert len(actual['collections']) == 2
    assert actual['collections'][0][0] == 'namespace.collection1'
    assert actual['collections'][0][1] == '>=1.0.0,<=2.0.0'
    assert actual['collections'][0][2].api_server == 'https://galaxy-dev.ansible.com'

    assert actual['collections'][1] == ('namespace.collection2', '*', None, 'galaxy')