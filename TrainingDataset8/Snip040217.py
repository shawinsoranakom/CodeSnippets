def test_dirfiles_sorts_files_and_ignores_hidden(self):
        dirfiles = util._dirfiles(self._test_dir.name, "*")
        filename_prefixes = [f[:2] for f in dirfiles.split("+")]
        assert filename_prefixes == ["01", "02", "03", "04"]