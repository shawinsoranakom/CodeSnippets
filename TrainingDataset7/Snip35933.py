def test_find_command_without_PATH(self):
        """
        find_command should still work when the PATH environment variable
        doesn't exist (#22256).
        """
        current_path = os.environ.pop("PATH", None)

        try:
            self.assertIsNone(find_command("_missing_"))
        finally:
            if current_path is not None:
                os.environ["PATH"] = current_path