def test_file_added(self):
        """
        When a file is added, it's returned by iter_all_python_module_files().
        """
        filename = self.temporary_file("test_deleted_removed_module.py")
        filename.touch()

        with extend_sys_path(str(filename.parent)):
            self.import_and_cleanup("test_deleted_removed_module")

        self.assertFileFound(filename.absolute())