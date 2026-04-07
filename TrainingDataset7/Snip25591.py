def test_fk_to_fk(self):
        self._test_explicit_related_name_clash(
            target=models.ForeignKey("Another", models.CASCADE),
            relative=models.ForeignKey("Target", models.CASCADE, related_name="clash"),
        )