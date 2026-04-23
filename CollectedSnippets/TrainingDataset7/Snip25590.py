def test_fk_to_integer(self):
        self._test_explicit_related_name_clash(
            target=models.IntegerField(),
            relative=models.ForeignKey("Target", models.CASCADE, related_name="clash"),
        )