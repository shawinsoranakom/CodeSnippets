def test_get_path_and_line_cached_property(self):
        path, line = github_links.get_path_and_line(
            module="tests.sphinx.testdata.package.module",
            fullname="MyClass.my_cached_property",
        )

        self.assertEqual(
            last_n_parts(path, 5), "tests/sphinx/testdata/package/module.py"
        )
        self.assertEqual(line, 20)