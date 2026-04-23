def test_empty_prefix(self):
        with self.assertRaisesMessage(
            ImproperlyConfigured, "Empty static prefix not permitted"
        ):
            static("")