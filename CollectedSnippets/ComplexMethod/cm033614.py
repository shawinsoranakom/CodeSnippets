def test_new_or_existing_module():
    module_name = 'blar.test.module'
    pkg_name = module_name.rpartition('.')[0]

    # create new module case
    nuke_module_prefix(module_name)
    with _AnsibleCollectionPkgLoaderBase._new_or_existing_module(module_name, __package__=pkg_name) as new_module:
        # the module we just created should now exist in sys.modules
        assert sys.modules.get(module_name) is new_module
        assert new_module.__name__ == module_name

    # the module should stick since we didn't raise an exception in the contextmgr
    assert sys.modules.get(module_name) is new_module

    # reuse existing module case
    with _AnsibleCollectionPkgLoaderBase._new_or_existing_module(module_name, __attr1__=42, blar='yo') as existing_module:
        assert sys.modules.get(module_name) is new_module  # should be the same module we created earlier
        assert hasattr(existing_module, '__package__') and existing_module.__package__ == pkg_name
        assert hasattr(existing_module, '__attr1__') and existing_module.__attr1__ == 42
        assert hasattr(existing_module, 'blar') and existing_module.blar == 'yo'

    # exception during update existing shouldn't zap existing module from sys.modules
    with pytest.raises(ValueError) as ve:
        with _AnsibleCollectionPkgLoaderBase._new_or_existing_module(module_name) as existing_module:
            err_to_raise = ValueError('bang')
            raise err_to_raise
    # make sure we got our error
    assert ve.value is err_to_raise
    # and that the module still exists
    assert sys.modules.get(module_name) is existing_module

    # test module removal after exception during creation
    nuke_module_prefix(module_name)
    with pytest.raises(ValueError) as ve:
        with _AnsibleCollectionPkgLoaderBase._new_or_existing_module(module_name) as new_module:
            err_to_raise = ValueError('bang')
            raise err_to_raise
    # make sure we got our error
    assert ve.value is err_to_raise
    # and that the module was removed
    assert sys.modules.get(module_name) is None