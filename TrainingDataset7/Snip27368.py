def test_alter_field_pk_fk_db_collation(self):
        """
        AlterField operation of db_collation on primary keys changes any FKs
        pointing to it.
        """
        collation = connection.features.test_collations.get("non_default")
        if not collation:
            self.skipTest("Language collations are not supported.")

        app_label = "test_alflpkfkdbc"
        project_state = self.apply_operations(
            app_label,
            ProjectState(),
            [
                migrations.CreateModel(
                    "Pony",
                    [
                        ("id", models.CharField(primary_key=True, max_length=10)),
                    ],
                ),
                migrations.CreateModel(
                    "Rider",
                    [
                        ("pony", models.ForeignKey("Pony", models.CASCADE)),
                    ],
                ),
                migrations.CreateModel(
                    "Stable",
                    [
                        ("ponies", models.ManyToManyField("Pony")),
                    ],
                ),
            ],
        )
        # State alteration.
        operation = migrations.AlterField(
            "Pony",
            "id",
            models.CharField(
                primary_key=True,
                max_length=10,
                db_collation=collation,
            ),
        )
        new_state = project_state.clone()
        operation.state_forwards(app_label, new_state)
        # Database alteration.
        with connection.schema_editor() as editor:
            operation.database_forwards(app_label, editor, project_state, new_state)
        self.assertColumnCollation(f"{app_label}_pony", "id", collation)
        self.assertColumnCollation(f"{app_label}_rider", "pony_id", collation)
        self.assertColumnCollation(f"{app_label}_stable_ponies", "pony_id", collation)
        # Reversal.
        with connection.schema_editor() as editor:
            operation.database_backwards(app_label, editor, new_state, project_state)