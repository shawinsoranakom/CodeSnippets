def test_root_loader():
    name = 'ansible_collections'
    # ensure this works even when ansible_collections doesn't exist on disk
    for paths in [], default_test_collection_paths:
        sys.modules.pop(name, None)
        loader = _AnsibleCollectionRootPkgLoader(name, paths)
        assert repr(loader).startswith('_AnsibleCollectionRootPkgLoader(path=')
        module = loader.load_module(name)
        assert module.__name__ == name
        assert module.__path__ == [p for p in extend_paths(paths, name) if os.path.isdir(p)]
        # even if the dir exists somewhere, this loader doesn't support get_data, so make __file__ a non-file
        assert module.__file__ == '<ansible_synthetic_collection_package>'
        assert module.__package__ == name
        assert sys.modules.get(name) == module