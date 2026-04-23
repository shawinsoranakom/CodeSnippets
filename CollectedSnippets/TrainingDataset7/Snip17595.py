def test_skips_backends_without_arguments(self):
        """
        A backend (SkippedBackend) is ignored if it doesn't accept the
        credentials as arguments.
        """
        self.assertEqual(authenticate(username="test", password="test"), self.user1)