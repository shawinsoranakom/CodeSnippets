def test_backend_import_error(self):
        """
        Failing to import a backend keeps raising the original import error
        (#24265).
        """
        with self.assertRaisesMessage(ImportError, "No module named 'raise"):
            engines.all()
        with self.assertRaisesMessage(ImportError, "No module named 'raise"):
            engines.all()