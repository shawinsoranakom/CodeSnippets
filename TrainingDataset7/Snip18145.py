def test_default_email(self):
        self.assertEqual(AbstractBaseUser.get_email_field_name(), "email")