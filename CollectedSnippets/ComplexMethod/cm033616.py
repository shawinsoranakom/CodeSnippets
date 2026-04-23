def test_finder_playbook_paths():
    finder = get_default_finder()
    reset_collections_loader_state(finder)

    import ansible_collections
    import ansible_collections.ansible
    import ansible_collections.testns

    # ensure the package modules look like we expect
    assert hasattr(ansible_collections, '__path__') and len(ansible_collections.__path__) > 0
    assert hasattr(ansible_collections.ansible, '__path__') and len(ansible_collections.ansible.__path__) > 0
    assert hasattr(ansible_collections.testns, '__path__') and len(ansible_collections.testns.__path__) > 0

    # these shouldn't be visible yet, since we haven't added the playbook dir
    with pytest.raises(ImportError):
        import ansible_collections.ansible.playbook_adj_other

    with pytest.raises(ImportError):
        import ansible_collections.testns.playbook_adj_other

    assert AnsibleCollectionConfig.playbook_paths == []
    playbook_path_fixture_dir = os.path.join(os.path.dirname(__file__), 'fixtures/playbook_path')

    # configure the playbook paths
    AnsibleCollectionConfig.playbook_paths = [playbook_path_fixture_dir]

    # playbook paths go to the front of the line
    assert AnsibleCollectionConfig.collection_paths[0] == os.path.join(playbook_path_fixture_dir, 'collections')

    # playbook paths should be updated on the existing root ansible_collections path, as well as on the 'ansible' namespace (but no others!)
    assert ansible_collections.__path__[0] == os.path.join(playbook_path_fixture_dir, 'collections/ansible_collections')
    assert ansible_collections.ansible.__path__[0] == os.path.join(playbook_path_fixture_dir, 'collections/ansible_collections/ansible')
    assert all('playbook_path' not in p for p in ansible_collections.testns.__path__)

    # should succeed since we fixed up the package path
    import ansible_collections.ansible.playbook_adj_other
    # should succeed since we didn't import freshns before hacking in the path
    import ansible_collections.freshns.playbook_adj_other
    # should fail since we've already imported something from this path and didn't fix up its package path
    with pytest.raises(ImportError):
        import ansible_collections.testns.playbook_adj_other