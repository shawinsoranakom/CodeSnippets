def test_validators(self):
        for validator, value, expected in TEST_DATA:
            name = (
                validator.__name__
                if isinstance(validator, types.FunctionType)
                else validator.__class__.__name__
            )
            exception_expected = expected is not None and issubclass(
                expected, Exception
            )
            with self.subTest(name, value=value):
                if (
                    validator is validate_image_file_extension
                    and not PILLOW_IS_INSTALLED
                ):
                    self.skipTest(
                        "Pillow is required to test validate_image_file_extension."
                    )
                if exception_expected:
                    with self.assertRaises(expected):
                        validator(value)
                else:
                    self.assertEqual(expected, validator(value))