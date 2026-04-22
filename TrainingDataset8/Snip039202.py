def test_git_repo_valid(self):
        with patch("git.repo.base.Repo.GitCommandWrapperType") as git_mock, patch(
            "streamlit.git_util.os"
        ):
            git_mock.return_value.version_info = (2, 20, 3)  # A recent git version
            repo = GitRepo(".")
            self.assertTrue(repo.is_valid())
            self.assertEqual((2, 20, 3), repo.git_version)