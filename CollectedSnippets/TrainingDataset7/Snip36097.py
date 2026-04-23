def test_choices(self):
        class Medal(TextChoices):
            GOLD = "GOLD", _("Gold")
            SILVER = "SILVER", _("Silver")
            BRONZE = "BRONZE", _("Bronze")

        expected = [
            ("GOLD", _("Gold")),
            ("SILVER", _("Silver")),
            ("BRONZE", _("Bronze")),
        ]
        self.assertEqual(normalize_choices(Medal), expected)