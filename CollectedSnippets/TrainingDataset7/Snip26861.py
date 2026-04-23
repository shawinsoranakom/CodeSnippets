def test_alter_regex_string_to_compiled_regex(self):
        regex_string = "^[a-z]+$"
        from_state = ModelState(
            "testapp",
            "model",
            [
                (
                    "id",
                    models.AutoField(
                        primary_key=True, validators=[RegexValidator(regex_string)]
                    ),
                )
            ],
        )
        to_state = ModelState(
            "testapp",
            "model",
            [
                (
                    "id",
                    models.AutoField(
                        primary_key=True,
                        validators=[RegexValidator(re.compile(regex_string))],
                    ),
                )
            ],
        )
        changes = self.get_changes([from_state], [to_state])
        self.assertNumberMigrations(changes, "testapp", 1)
        self.assertOperationTypes(changes, "testapp", 0, ["AlterField"])