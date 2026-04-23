def test_fk_to_integer(self):
        self._test_reverse_query_name_clash(
            target=models.IntegerField(),
            relative=models.ForeignKey("Target", models.CASCADE),
        )