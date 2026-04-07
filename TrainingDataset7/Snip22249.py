def test_field_value_coerce(self):
        """
        Test for tickets #8298, #9942 - Field values should be coerced into the
        correct type by the deserializer, not as part of the database write.
        """
        self.pre_save_checks = []
        signals.pre_save.connect(self.animal_pre_save_check)
        try:
            management.call_command(
                "loaddata",
                "animal.xml",
                verbosity=0,
            )
            self.assertEqual(
                self.pre_save_checks,
                [("Count = 42 (<class 'int'>)", "Weight = 1.2 (<class 'float'>)")],
            )
        finally:
            signals.pre_save.disconnect(self.animal_pre_save_check)