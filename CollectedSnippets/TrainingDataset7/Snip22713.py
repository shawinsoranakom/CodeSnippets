def test_custom_validator_longer_max_length(self):

        class CustomLongURLValidator(URLValidator):
            max_length = 4096

        class CustomURLField(URLField):
            default_validators = [CustomLongURLValidator()]

        field = CustomURLField()
        # A URL with 4096 chars is valid given the custom validator.
        prefix = "https://example.com/"
        url = prefix + "a" * (4096 - len(prefix))
        self.assertEqual(len(url), 4096)
        # No ValidationError is raised.
        field.clean(url)