def test_github_linkcode_resolve_link_to_object(self):
        info = {
            "module": "tests.sphinx.testdata.package.module",
            "fullname": "MyClass",
        }
        self.assertEqual(
            github_links.github_linkcode_resolve(
                "py", info, version="3.2", next_version="3.2"
            ),
            "https://github.com/django/django/blob/main/tests/sphinx/"
            "testdata/package/module.py#L12",
        )