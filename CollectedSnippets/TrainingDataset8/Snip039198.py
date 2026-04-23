def test_https_url_check(self):
        # standard https url with and without .git
        self.assertRegex("https://github.com/username/repo.git", GITHUB_HTTP_URL)
        self.assertRegex("https://github.com/username/repo", GITHUB_HTTP_URL)

        # with www with and without .git
        self.assertRegex("https://www.github.com/username/repo.git", GITHUB_HTTP_URL)
        self.assertRegex("https://www.github.com/username/repo", GITHUB_HTTP_URL)

        # not http
        self.assertNotRegex("http://www.github.com/username/repo.git", GITHUB_HTTP_URL)