def setUp(self):
        self._cwd = os.getcwd()
        self.work_dir = tempfile.mkdtemp(prefix="i18n_")
        # Resolve symlinks, if any, in test directory paths.
        self.test_dir = os.path.realpath(os.path.join(self.work_dir, self.work_subdir))
        copytree(os.path.join(source_code_dir, self.work_subdir), self.test_dir)
        # Step out of the temporary working tree before removing it to avoid
        # deletion problems on Windows. Cleanup actions registered with
        # addCleanup() are called in reverse so preserve this ordering.
        self.addCleanup(self._rmrf, self.test_dir)
        self.addCleanup(os.chdir, self._cwd)
        os.chdir(self.test_dir)