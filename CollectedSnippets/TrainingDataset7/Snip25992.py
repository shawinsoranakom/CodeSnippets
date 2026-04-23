def test_custom_related_name_reverse_empty_qs(self):
        self.assertQuerySetEqual(self.bob.custom.all(), [])