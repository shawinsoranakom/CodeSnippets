def test_m2m_to_fk(self):
        self._test_explicit_related_name_clash(
            target=models.ForeignKey("Another", models.CASCADE),
            relative=models.ManyToManyField("Target", related_name="clash"),
        )