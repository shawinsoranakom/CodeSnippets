def test_ssh_url_check(self):
        # standard ssh url
        self.assertRegex("git@github.com:username/repo.git", GITHUB_SSH_URL)

        # no .git
        self.assertRegex("git@github.com:username/repo", GITHUB_SSH_URL)