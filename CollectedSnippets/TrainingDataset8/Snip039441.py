def setUp(self):
        """Setup."""
        # Credentials._singleton should be None here, but a mis-behaving
        # test may have left it intact.
        Credentials._singleton = None