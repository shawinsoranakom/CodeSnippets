def test_get_path_and_line_forwarded_import_module(self):
        path, line = github_links.get_path_and_line(
            module="tests.sphinx.testdata.package.module",
            fullname="other_module.MyOtherClass",
        )

        self.assertEqual(
            last_n_parts(path, 5), "tests/sphinx/testdata/package/other_module.py"
        )
        self.assertEqual(line, 1)