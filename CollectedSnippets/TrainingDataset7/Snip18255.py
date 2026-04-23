def test_get_password_validators_custom(self):
        validator_config = [
            {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"}
        ]
        validators = get_password_validators(validator_config)
        self.assertEqual(len(validators), 1)
        self.assertEqual(validators[0].__class__.__name__, "CommonPasswordValidator")

        self.assertEqual(get_password_validators([]), [])