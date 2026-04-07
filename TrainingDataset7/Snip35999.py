def test_check_errors_catches_all_exceptions(self):
        """
        Since Python may raise arbitrary exceptions when importing code,
        check_errors() must catch Exception, not just some subclasses.
        """
        filename = self.temporary_file("test_exception.py")
        filename.write_text("raise Exception")
        with extend_sys_path(str(filename.parent)):
            try:
                with self.assertRaises(Exception):
                    autoreload.check_errors(import_module)("test_exception")
            finally:
                autoreload._exception = None
        self.assertFileFound(filename)