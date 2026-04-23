def test_m2m_to_m2m(self, related_name=None):
        self._test_explicit_related_query_name_clash(
            target=models.ManyToManyField("Another"),
            relative=models.ManyToManyField(
                "Target",
                related_name=related_name,
                related_query_name="clash",
            ),
        )