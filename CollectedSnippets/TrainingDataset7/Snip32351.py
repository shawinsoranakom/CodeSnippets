def test_import_error(self):
        msg = "Could not import '.....test' in 'tests.sphinx.testdata.package'."
        with self.assertRaisesMessage(ImportError, msg):
            github_links.get_path_and_line(
                module="tests.sphinx.testdata.package.import_error", fullname="Test"
            )