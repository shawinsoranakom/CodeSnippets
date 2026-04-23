def test_github_linkcode_resolve_unspecified_domain(self):
        domain = "unspecified"
        info = {}
        self.assertIsNone(
            github_links.github_linkcode_resolve(
                domain, info, version="3.2", next_version="3.2"
            )
        )