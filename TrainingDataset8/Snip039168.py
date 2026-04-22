def test_do_blacklist_user_configured_folders(self):
        """
        Files inside user configured folders should be blacklisted.
        """
        folder_black_list = FolderBlackList(["/bar/some_folder"])
        is_blacklisted = folder_black_list.is_blacklisted
        self.assertTrue(is_blacklisted("/bar/some_folder/script.py"))