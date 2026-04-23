def test_display_for_field_password_name_not_user_model(self):
        class PasswordModel(models.Model):
            password = models.CharField(max_length=200)

        password_field = PasswordModel._meta.get_field("password")
        display_value = display_for_field("test", password_field, self.empty_value)
        self.assertEqual(display_value, "test")