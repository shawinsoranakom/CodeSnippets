def test_get_password_validators_custom_invalid(self):
        validator_config = [{"NAME": "json.tool"}]
        msg = (
            "The module in NAME could not be imported: json.tool. "
            "Check your AUTH_PASSWORD_VALIDATORS setting."
        )
        with self.assertRaisesMessage(ImproperlyConfigured, msg):
            get_password_validators(validator_config)