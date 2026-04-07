def test_error_dict_is_json_serializable(self):
        init_errors = ErrorDict(
            [
                (
                    "__all__",
                    ErrorList(
                        [ValidationError("Sorry this form only works on leap days.")]
                    ),
                ),
                ("name", ErrorList([ValidationError("This field is required.")])),
            ]
        )
        min_value_error_list = ErrorList(
            [ValidationError("Ensure this value is greater than or equal to 0.")]
        )
        e = ErrorDict(
            init_errors,
            date=ErrorList(
                [
                    ErrorDict(
                        {
                            "day": min_value_error_list,
                            "month": min_value_error_list,
                            "year": min_value_error_list,
                        }
                    ),
                ]
            ),
        )
        e["renderer"] = ErrorList(
            [
                ValidationError(
                    "Select a valid choice. That choice is not one of the "
                    "available choices."
                ),
            ]
        )
        self.assertJSONEqual(
            json.dumps(e),
            {
                "__all__": ["Sorry this form only works on leap days."],
                "name": ["This field is required."],
                "date": [
                    {
                        "day": ["Ensure this value is greater than or equal to 0."],
                        "month": ["Ensure this value is greater than or equal to 0."],
                        "year": ["Ensure this value is greater than or equal to 0."],
                    },
                ],
                "renderer": [
                    "Select a valid choice. That choice is not one of the "
                    "available choices."
                ],
            },
        )