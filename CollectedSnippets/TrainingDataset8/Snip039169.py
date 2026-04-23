def test_do_not_blacklist(self):
        """
        Ensure we're not accidentally blacklisting things we shouldn't be.
        """
        folder_black_list = FolderBlackList([])
        is_blacklisted = folder_black_list.is_blacklisted

        self.assertFalse(is_blacklisted("/foo/not_blacklisted/script.py"))
        self.assertFalse(is_blacklisted("/foo/not_blacklisted/.hidden_script.py"))