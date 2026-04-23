def test_collection_default(collection_skeleton):
    meta_path = os.path.join(collection_skeleton, 'galaxy.yml')

    with open(meta_path, 'r') as galaxy_meta:
        metadata = yaml.safe_load(galaxy_meta)

    assert metadata['namespace'] == 'ansible_test'
    assert metadata['name'] == 'my_collection'
    assert metadata['authors'] == ['your name <example@domain.com>']
    assert metadata['readme'] == 'README.md'
    assert metadata['version'] == '1.0.0'
    assert metadata['description'] == 'your collection description'
    assert metadata['license'] == ['GPL-2.0-or-later']
    assert metadata['tags'] == []
    assert metadata['dependencies'] == {}
    assert metadata['documentation'] == 'http://docs.example.com'
    assert metadata['repository'] == 'http://example.com/repository'
    assert metadata['homepage'] == 'http://example.com'
    assert metadata['issues'] == 'http://example.com/issue/tracker'

    for d in ['docs', 'plugins', 'roles']:
        assert os.path.isdir(os.path.join(collection_skeleton, d)), \
            "Expected collection subdirectory {0} doesn't exist".format(d)