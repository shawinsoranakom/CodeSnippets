def test_default_auto_field_setting_none(self):
        msg = "DEFAULT_AUTO_FIELD must not be empty."
        with self.assertRaisesMessage(ImproperlyConfigured, msg):

            class Model(models.Model):
                pass