def test_smallfield_bigautofield_foreignfield_growth(self):
        """A field may be migrated from SmallAutoField to BigAutoField."""
        self._test_autofield_foreignfield_growth(
            models.SmallAutoField,
            models.BigAutoField,
            2**33,
        )