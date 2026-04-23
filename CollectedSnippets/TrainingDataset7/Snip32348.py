def test_github_linkcode_resolve_not_found(self):
        info = {
            "module": "foo.bar.baz.hopefully_non_existant_module",
            "fullname": "MyClass",
        }
        self.assertIsNone(
            github_links.github_linkcode_resolve(
                "py", info, version="3.2", next_version="3.2"
            )
        )