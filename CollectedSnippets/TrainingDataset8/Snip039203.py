def test_gitpython_not_installed(self):
        with patch.dict("sys.modules", {"git": None}):
            repo = GitRepo(".")
            self.assertFalse(repo.is_valid())