def test_create_model_constraint_percent_escaping(self):
        app_label = "add_constraint_string_quoting"
        from_state = ProjectState()
        checks = [
            # "%" generated in startswith lookup should be escaped in a way
            # that is considered a leading wildcard.
            (
                models.Q(name__startswith="Albert"),
                {"name": "Alberta"},
                {"name": "Artur"},
            ),
            # Literal "%" should be escaped in a way that is not a considered a
            # wildcard.
            (models.Q(rebate__endswith="%"), {"rebate": "10%"}, {"rebate": "10%$"}),
            # Right-hand-side baked "%" literals should not be used for
            # parameters interpolation.
            (
                ~models.Q(surname__startswith=models.F("name")),
                {"name": "Albert"},
                {"name": "Albert", "surname": "Alberto"},
            ),
            # Exact matches against "%" literals should also be supported.
            (
                models.Q(name="%"),
                {"name": "%"},
                {"name": "Albert"},
            ),
        ]
        for check, valid, invalid in checks:
            with self.subTest(condition=check, valid=valid, invalid=invalid):
                constraint = models.CheckConstraint(condition=check, name="constraint")
                operation = migrations.CreateModel(
                    "Author",
                    fields=[
                        ("id", models.AutoField(primary_key=True)),
                        ("name", models.CharField(max_length=100)),
                        ("surname", models.CharField(max_length=100, db_default="")),
                        ("rebate", models.CharField(max_length=100)),
                    ],
                    options={"constraints": [constraint]},
                )
                to_state = from_state.clone()
                operation.state_forwards(app_label, to_state)
                with connection.schema_editor() as editor:
                    operation.database_forwards(app_label, editor, from_state, to_state)
                Author = to_state.apps.get_model(app_label, "Author")
                try:
                    with transaction.atomic():
                        Author.objects.create(**valid).delete()
                    with self.assertRaises(IntegrityError), transaction.atomic():
                        Author.objects.create(**invalid)
                finally:
                    with connection.schema_editor() as editor:
                        migrations.DeleteModel("Author").database_forwards(
                            app_label, editor, to_state, from_state
                        )