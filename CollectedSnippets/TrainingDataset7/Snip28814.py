def test_default_auto_field_setting(self):
        class Model(models.Model):
            pass

        self.assertIsInstance(Model._meta.pk, models.SmallAutoField)