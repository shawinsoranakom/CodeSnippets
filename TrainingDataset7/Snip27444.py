def test_smallfield_autofield_foreignfield_growth(self):
        """A field may be migrated from SmallAutoField to AutoField."""
        self._test_autofield_foreignfield_growth(
            models.SmallAutoField,
            models.AutoField,
            2**22,
        )