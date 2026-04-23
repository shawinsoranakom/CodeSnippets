def test_do_blacklist(self):
        """
        miniconda, anaconda, and .*/ folders should be blacklisted.
        """
        folder_black_list = FolderBlackList([])
        is_blacklisted = folder_black_list.is_blacklisted

        self.assertTrue(is_blacklisted("/foo/miniconda2/script.py"))
        self.assertTrue(is_blacklisted("/foo/miniconda3/script.py"))
        self.assertTrue(is_blacklisted("/foo/anaconda2/script.py"))
        self.assertTrue(is_blacklisted("/foo/anaconda3/script.py"))
        self.assertTrue(is_blacklisted("/foo/.virtualenv/script.py"))
        self.assertTrue(is_blacklisted("/foo/.venv/script.py"))
        self.assertTrue(is_blacklisted("/foo/.random_hidden_folder/script.py"))