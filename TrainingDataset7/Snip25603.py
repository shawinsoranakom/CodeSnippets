def test_m2m_to_integer(self, related_name=None):
        self._test_explicit_related_query_name_clash(
            target=models.IntegerField(),
            relative=models.ManyToManyField(
                "Target", related_name=related_name, related_query_name="clash"
            ),
        )