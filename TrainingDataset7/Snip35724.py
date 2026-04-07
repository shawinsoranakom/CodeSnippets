def test_warning_override_converter(self):
        msg = "Converter 'base64' is already registered."
        try:
            with self.assertRaisesMessage(ValueError, msg):
                register_converter(Base64Converter, "base64")
                register_converter(Base64Converter, "base64")
        finally:
            REGISTERED_CONVERTERS.pop("base64", None)