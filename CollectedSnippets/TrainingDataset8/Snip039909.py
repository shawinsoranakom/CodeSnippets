def reload_secrets(_: int) -> None:
            # Reset secrets, and then access a secret to reparse.
            self.secrets._reset()
            self.assertEqual(self.secrets["db_username"], "Jane")