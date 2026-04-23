def test_get_redirect_field_name_default(self):
        redirect_field_name = self.middleware.get_redirect_field_name(lambda: None)
        self.assertEqual(redirect_field_name, REDIRECT_FIELD_NAME)