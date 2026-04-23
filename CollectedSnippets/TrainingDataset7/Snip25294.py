def test_CommaSeparatedIntegerField_deprecated(self):
        class CommaSeparatedIntegerModel(models.Model):
            csi = models.CommaSeparatedIntegerField(max_length=64)

        model = CommaSeparatedIntegerModel()
        self.assertEqual(
            model.check(),
            [
                checks.Error(
                    "CommaSeparatedIntegerField is removed except for support in "
                    "historical migrations.",
                    hint=(
                        "Use "
                        "CharField(validators=[validate_comma_separated_integer_list]) "
                        "instead."
                    ),
                    obj=CommaSeparatedIntegerModel._meta.get_field("csi"),
                    id="fields.E901",
                )
            ],
        )