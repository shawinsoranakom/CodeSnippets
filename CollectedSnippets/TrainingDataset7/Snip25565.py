def test_related_field_has_invalid_related_name(self):
        digit = 0
        illegal_non_alphanumeric = "!"
        whitespace = "\t"

        invalid_related_names = [
            "%s_begins_with_digit" % digit,
            "%s_begins_with_illegal_non_alphanumeric" % illegal_non_alphanumeric,
            "%s_begins_with_whitespace" % whitespace,
            "contains_%s_illegal_non_alphanumeric" % illegal_non_alphanumeric,
            "contains_%s_whitespace" % whitespace,
            "ends_with_with_illegal_non_alphanumeric_%s" % illegal_non_alphanumeric,
            "ends_with_whitespace_%s" % whitespace,
            "with",  # a Python keyword
            "related_name\n",
            "",
            "，",  # non-ASCII
        ]

        class Parent(models.Model):
            pass

        for invalid_related_name in invalid_related_names:
            Child = type(
                "Child%s" % invalid_related_name,
                (models.Model,),
                {
                    "parent": models.ForeignKey(
                        "Parent", models.CASCADE, related_name=invalid_related_name
                    ),
                    "__module__": Parent.__module__,
                },
            )

            field = Child._meta.get_field("parent")
            self.assertEqual(
                Child.check(),
                [
                    Error(
                        "The name '%s' is invalid related_name for field Child%s.parent"
                        % (invalid_related_name, invalid_related_name),
                        hint=(
                            "Related name must be a valid Python identifier or end "
                            "with a '+'"
                        ),
                        obj=field,
                        id="fields.E306",
                    ),
                ],
            )