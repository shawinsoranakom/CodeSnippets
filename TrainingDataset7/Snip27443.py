def test_autofield__bigautofield_foreignfield_growth(self):
        """A field may be migrated from AutoField to BigAutoField."""
        self._test_autofield_foreignfield_growth(
            models.AutoField,
            models.BigAutoField,
            2**33,
        )