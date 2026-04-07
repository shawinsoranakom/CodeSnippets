def test_get_path_and_line_wildcard_import(self):
        path, line = github_links.get_path_and_line(
            module="tests.sphinx.testdata.package.module", fullname="WildcardClass"
        )

        self.assertEqual(
            last_n_parts(path, 5),
            "tests/sphinx/testdata/package/wildcard_module.py",
        )
        self.assertEqual(line, 4)

        path, line = github_links.get_path_and_line(
            module="tests.sphinx.testdata.package.module",
            fullname="WildcardMixin",
        )
        self.assertEqual(
            last_n_parts(path, 5),
            "tests/sphinx/testdata/package/wildcard_base.py",
        )
        self.assertEqual(line, 1)