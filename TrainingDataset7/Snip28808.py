def test_default_auto_field_setting_nonexistent(self):
        msg = (
            "DEFAULT_AUTO_FIELD refers to the module "
            "'django.db.models.NonexistentAutoField' that could not be "
            "imported."
        )
        with self.assertRaisesMessage(ImproperlyConfigured, msg):

            class Model(models.Model):
                pass