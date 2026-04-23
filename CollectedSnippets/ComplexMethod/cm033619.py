def test_importlib_resources():
    from importlib.resources import files
    from pathlib import Path

    f = get_default_finder()
    reset_collections_loader_state(f)

    ansible_collections_ns = files('ansible_collections')
    ansible_ns = files('ansible_collections.ansible')
    testns = files('ansible_collections.testns')
    testcoll = files('ansible_collections.testns.testcoll')
    testcoll2 = files('ansible_collections.testns.testcoll2')
    module_utils = files('ansible_collections.testns.testcoll.plugins.module_utils')

    assert isinstance(ansible_collections_ns, _AnsibleNSTraversable)
    assert isinstance(ansible_ns, _AnsibleNSTraversable)
    assert isinstance(testcoll, Path)
    assert isinstance(module_utils, Path)

    assert ansible_collections_ns.is_dir()
    assert ansible_ns.is_dir()
    assert testcoll.is_dir()
    assert module_utils.is_dir()

    first_path = Path(default_test_collection_paths[0])
    second_path = Path(default_test_collection_paths[1])
    testns_paths = []
    ansible_ns_paths = []
    for path in default_test_collection_paths[:2]:
        ansible_ns_paths.append(Path(path) / 'ansible_collections' / 'ansible')
        testns_paths.append(Path(path) / 'ansible_collections' / 'testns')

    assert testns._paths == testns_paths
    # NOTE: The next two asserts check for subsets to accommodate running the unit tests when externally installed collections are available.
    assert set(ansible_ns_paths).issubset(ansible_ns._paths)
    assert set(Path(p) / 'ansible_collections' for p in default_test_collection_paths[:2]).issubset(ansible_collections_ns._paths)
    assert testcoll2 == second_path / 'ansible_collections' / 'testns' / 'testcoll2'

    assert {p.name for p in module_utils.glob('*.py')} == {'__init__.py', 'my_other_util.py', 'my_util.py'}
    nestcoll_mu_init = first_path / 'ansible_collections' / 'testns' / 'testcoll' / 'plugins' / 'module_utils' / '__init__.py'
    assert next(module_utils.glob('__init__.py')) == nestcoll_mu_init