def test_default_value_of_default_auto_field_setting(self):
        """django.conf.global_settings defaults to BigAutoField."""

        class MyModel(models.Model):
            pass

        self.assertIsInstance(MyModel._meta.pk, models.BigAutoField)