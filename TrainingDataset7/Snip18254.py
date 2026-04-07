def test_get_default_password_validators(self):
        validators = get_default_password_validators()
        self.assertEqual(len(validators), 2)
        self.assertEqual(validators[0].__class__.__name__, "CommonPasswordValidator")
        self.assertEqual(validators[1].__class__.__name__, "MinimumLengthValidator")
        self.assertEqual(validators[1].min_length, 12)