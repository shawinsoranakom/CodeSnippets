def test_app_default_auto_field_none(self):
        msg = (
            "model_options.apps.ModelPKNoneConfig.default_auto_field must not "
            "be empty."
        )
        with self.assertRaisesMessage(ImproperlyConfigured, msg):

            class Model(models.Model):
                pass