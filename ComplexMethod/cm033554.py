def test_parse_requirements_with_roles_and_collections(requirements_cli, requirements_file):
    actual = requirements_cli._parse_requirements_file(requirements_file)
    actual['collections'] = [('%s.%s' % (r.namespace, r.name), r.ver, r.src, r.type,) for r in actual.get('collections', [])]

    assert len(actual['roles']) == 3
    assert actual['roles'][0].name == 'username.role_name'
    assert actual['roles'][1].name == 'username2.role_name2'
    assert actual['roles'][2].name == 'repo'
    assert actual['roles'][2].src == 'ssh://github.com/user/repo'

    assert len(actual['collections']) == 1
    assert actual['collections'][0] == ('namespace.collection2', '*', None, 'galaxy')