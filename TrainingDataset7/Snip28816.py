def test_app_default_auto_field(self):
        class Model(models.Model):
            pass

        self.assertIsInstance(Model._meta.pk, models.SmallAutoField)