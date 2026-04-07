def test_default_auto_field_setting_bigautofield_subclass(self):
        class Model(models.Model):
            pass

        self.assertIsInstance(Model._meta.pk, MyBigAutoField)