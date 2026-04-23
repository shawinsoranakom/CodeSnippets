def test_rmtree_deleted_race_condition(self):
        # bpo-37260
        #
        # Test that a file or a directory deleted after it is enumerated
        # by scandir() but before unlink() or rmdr() is called doesn't
        # generate any errors.
        def _onexc(fn, path, exc):
            assert fn in (os.rmdir, os.unlink)
            if not isinstance(exc, PermissionError):
                raise
            # Make the parent and the children writeable.
            for p, mode in zip(paths, old_modes):
                os.chmod(p, mode)
            # Remove other dirs except one.
            keep = next(p for p in dirs if p != path)
            for p in dirs:
                if p != keep:
                    os.rmdir(p)
            # Remove other files except one.
            keep = next(p for p in files if p != path)
            for p in files:
                if p != keep:
                    os.unlink(p)

        os.mkdir(TESTFN)
        paths = [TESTFN] + [os.path.join(TESTFN, f'child{i}')
                            for i in range(6)]
        dirs = paths[1::2]
        files = paths[2::2]
        for path in dirs:
            os.mkdir(path)
        for path in files:
            create_file(path)

        old_modes = [os.stat(path).st_mode for path in paths]

        # Make the parent and the children non-writeable.
        new_mode = stat.S_IREAD|stat.S_IEXEC
        for path in reversed(paths):
            os.chmod(path, new_mode)

        try:
            shutil.rmtree(TESTFN, onexc=_onexc)
        except:
            # Test failed, so cleanup artifacts.
            for path, mode in zip(paths, old_modes):
                try:
                    os.chmod(path, mode)
                except OSError:
                    pass
            shutil.rmtree(TESTFN)
            raise