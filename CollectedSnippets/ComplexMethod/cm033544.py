def test_collection_skeleton(collection_skeleton):
    meta_path = os.path.join(collection_skeleton, 'galaxy.yml')

    with open(meta_path, 'r') as galaxy_meta:
        metadata = yaml.safe_load(galaxy_meta)

    assert metadata['namespace'] == 'ansible_test'
    assert metadata['name'] == 'delete_me_skeleton'
    assert metadata['authors'] == ['Ansible Cow <acow@bovineuniversity.edu>', 'Tu Cow <tucow@bovineuniversity.edu>']
    assert metadata['version'] == '0.1.0'
    assert metadata['readme'] == 'README.md'
    assert len(metadata) == 5

    assert os.path.exists(os.path.join(collection_skeleton, 'README.md'))

    # Test empty directories exist and are empty
    for empty_dir in ['plugins/action', 'plugins/filter', 'plugins/inventory', 'plugins/lookup',
                      'plugins/module_utils', 'plugins/modules']:

        assert os.listdir(os.path.join(collection_skeleton, empty_dir)) == []

    # Test files that don't end with .j2 were not templated
    doc_file = os.path.join(collection_skeleton, 'docs', 'My Collection.md')
    with open(doc_file, 'r') as f:
        doc_contents = f.read()
    assert doc_contents.strip() == 'Welcome to my test collection doc for {{ namespace }}.'

    # Test files that end with .j2 but are in the templates directory were not templated
    for template_dir in ['playbooks/templates', 'playbooks/templates/subfolder',
                         'roles/common/templates', 'roles/common/templates/subfolder']:
        test_conf_j2 = os.path.join(collection_skeleton, template_dir, 'test.conf.j2')
        assert os.path.exists(test_conf_j2)

        with open(test_conf_j2, 'r') as f:
            contents = f.read()
        expected_contents = '[defaults]\ntest_key = {{ test_variable }}'

        assert expected_contents == contents.strip()