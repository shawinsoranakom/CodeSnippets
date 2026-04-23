def test_warning_override_default_converter(self):
        msg = "Converter 'int' is already registered."
        with self.assertRaisesMessage(ValueError, msg):
            register_converter(IntConverter, "int")