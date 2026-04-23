def test_nspkg_loader_load_module():
    # ensure the loader behaves on the toplevel and ansible packages for both legit and missing/bogus paths
    for name in ['ansible_collections.ansible', 'ansible_collections.testns']:
        parent_pkg = name.partition('.')[0]
        module_to_load = name.rpartition('.')[2]
        paths = extend_paths(default_test_collection_paths, parent_pkg)
        existing_child_paths = [p for p in extend_paths(paths, module_to_load) if os.path.exists(p)]
        sys.modules.pop(name, None)
        loader = _AnsibleCollectionNSPkgLoader(name, path_list=paths)
        assert repr(loader).startswith('_AnsibleCollectionNSPkgLoader(path=')
        module = loader.load_module(name)
        assert module.__name__ == name
        assert isinstance(module.__loader__, _AnsibleCollectionNSPkgLoader)
        assert module.__path__ == existing_child_paths
        assert module.__package__ == name
        assert module.__file__ == '<ansible_synthetic_collection_package>'
        assert sys.modules.get(name) == module