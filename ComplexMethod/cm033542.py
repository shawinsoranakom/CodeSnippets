def test_ansible_version(capsys):
    adhoc_cli = AdHocCLI(args=['/bin/ansible', '--version'])
    with pytest.raises(SystemExit):
        adhoc_cli.run()
    version = capsys.readouterr()
    version_lines = version.out.splitlines()

    assert len(version_lines) == 9, 'Incorrect number of lines in "ansible --version" output'
    assert re.match(r'ansible \[core [0-9.a-z]+\]', version_lines[0]), 'Incorrect ansible version line in "ansible --version" output'
    assert re.match('  config file = .*$', version_lines[1]), 'Incorrect config file line in "ansible --version" output'
    assert re.match('  configured module search path = .*$', version_lines[2]), 'Incorrect module search path in "ansible --version" output'
    assert re.match('  ansible python module location = .*$', version_lines[3]), 'Incorrect python module location in "ansible --version" output'
    assert re.match('  ansible collection location = .*$', version_lines[4]), 'Incorrect collection location in "ansible --version" output'
    assert re.match('  executable location = .*$', version_lines[5]), 'Incorrect executable locaction in "ansible --version" output'
    assert re.match('  python version = .*$', version_lines[6]), 'Incorrect python version in "ansible --version" output'
    assert re.match('  jinja version = .*$', version_lines[7]), 'Incorrect jinja version in "ansible --version" output'
    assert re.match('  pyyaml version = .*$', version_lines[8]), 'Missing pyyaml version in "ansible --version" output'