def test_urlconf_was_reverted(self):
        """URLconf is reverted to original value after modification in a
        TestCase

        This will not find a match as the default ROOT_URLCONF is empty.
        """
        with self.assertRaises(NoReverseMatch):
            reverse("arg_view", args=["somename"])