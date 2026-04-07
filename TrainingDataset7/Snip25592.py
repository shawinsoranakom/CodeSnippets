def test_fk_to_m2m(self):
        self._test_explicit_related_name_clash(
            target=models.ManyToManyField("Another"),
            relative=models.ForeignKey("Target", models.CASCADE, related_name="clash"),
        )