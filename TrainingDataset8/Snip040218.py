def test_dirfiles_glob_pattern(self):
        dirfiles = util._dirfiles(self._test_dir.name, "*.py")
        filename_prefixes = [f[:2] for f in dirfiles.split("+")]
        assert filename_prefixes == ["01", "02", "03"]