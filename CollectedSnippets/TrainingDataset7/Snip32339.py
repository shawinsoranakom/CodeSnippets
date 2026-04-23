def test_get_path_and_line_method(self):
        path, line = github_links.get_path_and_line(
            module="tests.sphinx.testdata.package.module", fullname="MyClass.my_method"
        )

        self.assertEqual(
            last_n_parts(path, 5), "tests/sphinx/testdata/package/module.py"
        )
        self.assertEqual(line, 16)