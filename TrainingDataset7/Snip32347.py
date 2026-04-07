def test_github_linkcode_resolve_unspecified_info(self):
        domain = "py"
        info = {"module": None, "fullname": None}
        self.assertIsNone(
            github_links.github_linkcode_resolve(
                domain, info, version="3.2", next_version="3.2"
            )
        )