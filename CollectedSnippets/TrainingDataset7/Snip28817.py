def test_m2m_default_auto_field_setting(self):
        class M2MModel(models.Model):
            m2m = models.ManyToManyField("self")

        m2m_pk = M2MModel._meta.get_field("m2m").remote_field.through._meta.pk
        self.assertIsInstance(m2m_pk, models.SmallAutoField)