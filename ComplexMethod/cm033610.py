def test_loader_install():
    fake_mp = [MagicMock(), _AnsibleCollectionFinder(), MagicMock(), _AnsibleCollectionFinder()]
    fake_ph = [MagicMock().m1, MagicMock().m2, _AnsibleCollectionFinder()._ansible_collection_path_hook, NonCallableMagicMock]
    # must nest until 2.6 compilation is totally donezo
    with patch.object(sys, 'meta_path', fake_mp):
        with patch.object(sys, 'path_hooks', fake_ph):
            f = _AnsibleCollectionFinder()
            f._install()
            assert len(sys.meta_path) == 3  # should have removed the existing ACFs and installed a new one
            assert sys.meta_path[0] is f  # at the front
            # the rest of the meta_path should not be AnsibleCollectionFinders
            assert all((not isinstance(mpf, _AnsibleCollectionFinder) for mpf in sys.meta_path[1:]))
            assert len(sys.path_hooks) == 4  # should have removed the existing ACF path hooks and installed a new one
            # the first path hook should be ours, make sure it's pointing at the right instance
            assert hasattr(sys.path_hooks[0], '__self__') and sys.path_hooks[0].__self__ is f
            # the rest of the path_hooks should not point at an AnsibleCollectionFinder
            assert all((not isinstance(ph.__self__, _AnsibleCollectionFinder) for ph in sys.path_hooks[1:] if hasattr(ph, '__self__')))
            assert AnsibleCollectionConfig.collection_finder is f
            with pytest.raises(ValueError):
                AnsibleCollectionConfig.collection_finder = f