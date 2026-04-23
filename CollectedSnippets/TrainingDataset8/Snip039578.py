def test_magic_mock(self):
        """Test that MagicMocks never hash to the same thing."""
        # (This also tests that MagicMock can hash at all, without blowing the
        # stack due to an infinite recursion.)
        self.assertNotEqual(get_hash(MagicMock()), get_hash(MagicMock()))