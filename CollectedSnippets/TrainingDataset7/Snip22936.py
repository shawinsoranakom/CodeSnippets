def __init__(self, *args, **kwargs):
                fields = (
                    CharField(
                        label="Country Code",
                        validators=[
                            RegexValidator(
                                r"^\+[0-9]{1,2}$", message="Enter a valid country code."
                            )
                        ],
                    ),
                    CharField(label="Phone Number"),
                    CharField(
                        label="Extension",
                        error_messages={"incomplete": "Enter an extension."},
                    ),
                    CharField(
                        label="Label", required=False, help_text="E.g. home, work."
                    ),
                )
                super().__init__(fields, *args, **kwargs)