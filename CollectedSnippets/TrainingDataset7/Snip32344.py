def test_get_branch_stable(self):
        branch = github_links.get_branch(version="2.2", next_version="3.2")
        self.assertEqual(branch, "stable/2.2.x")