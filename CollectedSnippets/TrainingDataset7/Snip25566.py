def test_related_field_has_valid_related_name(self):
        lowercase = "a"
        uppercase = "A"
        digit = 0

        related_names = [
            "%s_starts_with_lowercase" % lowercase,
            "%s_tarts_with_uppercase" % uppercase,
            "_starts_with_underscore",
            "contains_%s_digit" % digit,
            "ends_with_plus+",
            "_+",
            "+",
            "試",
            "試驗+",
        ]

        class Parent(models.Model):
            pass

        for related_name in related_names:
            Child = type(
                "Child%s" % related_name,
                (models.Model,),
                {
                    "parent": models.ForeignKey(
                        "Parent", models.CASCADE, related_name=related_name
                    ),
                    "__module__": Parent.__module__,
                },
            )
            self.assertEqual(Child.check(), [])