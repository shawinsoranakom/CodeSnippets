def test_print_old_git_warning(self, mock_git_repo):
        mock_git_repo.return_value.is_valid.return_value = False
        mock_git_repo.return_value.git_version = (1, 2, 3)

        bootstrap._maybe_print_old_git_warning("main_script_path")
        out = sys.stdout.getvalue()
        self.assertIn("Streamlit requires Git 2.7.0 or later, but you have 1.2.3.", out)