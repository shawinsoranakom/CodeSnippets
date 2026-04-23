def test_custom_test_client(self):
        """A test case can specify a custom class for self.client."""
        self.assertIs(hasattr(self.client, "i_am_customized"), True)