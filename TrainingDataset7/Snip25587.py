def test_m2m_to_m2m(self):
        self._test_reverse_query_name_clash(
            target=models.ManyToManyField("Another"),
            relative=models.ManyToManyField("Target"),
        )