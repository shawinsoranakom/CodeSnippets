def test_zip_reload(self):
        """
        Modules imported from zipped files have their archive location included
        in the result.
        """
        zip_file = self.temporary_file("zip_import.zip")
        with zipfile.ZipFile(str(zip_file), "w", zipfile.ZIP_DEFLATED) as zipf:
            zipf.writestr("test_zipped_file.py", "")

        with extend_sys_path(str(zip_file)):
            self.import_and_cleanup("test_zipped_file")
        self.assertFileFound(zip_file)