def test_fk_to_fk(self):
        self._test_accessor_clash(
            target=models.ForeignKey("Another", models.CASCADE),
            relative=models.ForeignKey("Target", models.CASCADE),
        )