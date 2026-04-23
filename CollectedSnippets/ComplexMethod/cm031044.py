def test_makefile_test_folders(self):
        test_dirs = self.list_test_dirs()
        idle_test = 'idlelib/idle_test'
        self.assertIn(idle_test, test_dirs)

        used = set([idle_test])
        for dirpath, dirs, files in os.walk(support.TEST_HOME_DIR):
            dirname = os.path.basename(dirpath)
            # Skip temporary dirs:
            if dirname == '__pycache__' or dirname.startswith('.'):
                dirs.clear()  # do not process subfolders
                continue

            # Skip empty dirs (ignoring hidden files and __pycache__):
            files = [
                filename for filename in files
                if not filename.startswith('.')
            ]
            dirs = [
                dirname for dirname in dirs
                if not dirname.startswith('.') and dirname != "__pycache__"
            ]
            if not dirs and not files:
                continue

            relpath = os.path.relpath(dirpath, support.STDLIB_DIR)
            with self.subTest(relpath=relpath):
                self.assertIn(
                    relpath,
                    test_dirs,
                    msg=(
                        f"{relpath!r} is not included in the Makefile's list "
                        "of test directories to install"
                    )
                )
                used.add(relpath)

        # Don't check the wheel dir when Python is built --with-wheel-pkg-dir
        if sysconfig.get_config_var('WHEEL_PKG_DIR'):
            test_dirs.remove('test/wheeldata')
            used.discard('test/wheeldata')

        # Check that there are no extra entries:
        unique_test_dirs = set(test_dirs)
        self.assertSetEqual(unique_test_dirs, used)
        self.assertEqual(len(test_dirs), len(unique_test_dirs))