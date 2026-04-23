def _file_should_be_watched(self, filepath):
        # Using short circuiting for performance.
        return self._file_is_new(filepath) and (
            file_util.file_is_in_folder_glob(filepath, self._script_folder)
            or file_util.file_in_pythonpath(filepath)
        )