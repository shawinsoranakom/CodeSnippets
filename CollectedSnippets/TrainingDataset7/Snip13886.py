def assertWarnsMessage(self, expected_warning, expected_message, *args, **kwargs):
        """
        Same as assertRaisesMessage but for assertWarns() instead of
        assertRaises().
        """
        return self._assertFooMessage(
            self.assertWarns,
            "warning",
            expected_warning,
            expected_message,
            *args,
            **kwargs,
        )