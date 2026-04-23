def test_fk_to_m2m(self):
        self._test_reverse_query_name_clash(
            target=models.ManyToManyField("Another"),
            relative=models.ForeignKey("Target", models.CASCADE),
        )