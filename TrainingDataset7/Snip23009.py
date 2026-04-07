def test_management_form_field_names(self):
        """The management form class has field names matching the constants."""
        self.assertCountEqual(
            ManagementForm.base_fields,
            [
                TOTAL_FORM_COUNT,
                INITIAL_FORM_COUNT,
                MIN_NUM_FORM_COUNT,
                MAX_NUM_FORM_COUNT,
            ],
        )