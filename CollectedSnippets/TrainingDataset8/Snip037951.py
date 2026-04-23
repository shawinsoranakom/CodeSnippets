def _file_should_be_hashed(self, filename: str) -> bool:
        global _FOLDER_BLACK_LIST

        if not _FOLDER_BLACK_LIST:
            _FOLDER_BLACK_LIST = FolderBlackList(
                config.get_option("server.folderWatchBlacklist")
            )

        filepath = os.path.abspath(filename)
        file_is_blacklisted = _FOLDER_BLACK_LIST.is_blacklisted(filepath)
        # Short circuiting for performance.
        if file_is_blacklisted:
            return False
        return file_util.file_is_in_folder_glob(
            filepath, self._get_main_script_directory()
        ) or file_util.file_in_pythonpath(filepath)