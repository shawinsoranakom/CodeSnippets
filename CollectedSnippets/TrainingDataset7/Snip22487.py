def test_strip_before_checking_empty(self):
        """
        A whitespace-only value, ' ', is stripped to an empty string and then
        converted to the empty value, None.
        """
        f = CharField(required=False, empty_value=None)
        self.assertIsNone(f.clean(" "))