def test_m2m_to_m2m(self):
        self._test_explicit_related_name_clash(
            target=models.ManyToManyField("Another"),
            relative=models.ManyToManyField("Target", related_name="clash"),
        )