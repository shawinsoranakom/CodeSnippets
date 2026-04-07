def test_get_branch_latest(self):
        branch = github_links.get_branch(version="3.2", next_version="3.2")
        self.assertEqual(branch, "main")