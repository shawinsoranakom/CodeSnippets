def test_fk_to_fk(self):
        self._test_reverse_query_name_clash(
            target=models.ForeignKey("Another", models.CASCADE),
            relative=models.ForeignKey("Target", models.CASCADE),
        )