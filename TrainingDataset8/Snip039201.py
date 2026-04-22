def test_old_git_version(self):
        """If the installed git is older than 2.7, certain repo operations
        prompt the user for credentials. We don't want to do this, so
        repo.is_valid() returns False for old gits.
        """
        with patch("git.repo.base.Repo.GitCommandWrapperType") as git_mock, patch(
            "streamlit.git_util.os"
        ):
            git_mock.return_value.version_info = (1, 6, 4)  # An old git version
            repo = GitRepo(".")
            self.assertFalse(repo.is_valid())
            self.assertEqual((1, 6, 4), repo.git_version)