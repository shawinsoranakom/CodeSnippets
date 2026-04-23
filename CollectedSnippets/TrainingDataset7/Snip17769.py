def test_success(self):
        # The success case
        data = {
            "username": "testclient",
            "password": "password",
        }
        form = AuthenticationForm(None, data)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.non_field_errors(), [])