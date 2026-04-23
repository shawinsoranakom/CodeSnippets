def test_m2m_to_integer(self):
        self._test_explicit_related_name_clash(
            target=models.IntegerField(),
            relative=models.ManyToManyField("Target", related_name="clash"),
        )