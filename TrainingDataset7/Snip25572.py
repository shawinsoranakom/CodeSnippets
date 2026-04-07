def test_fk_to_integer(self):
        self._test_accessor_clash(
            target=models.IntegerField(),
            relative=models.ForeignKey("Target", models.CASCADE),
        )