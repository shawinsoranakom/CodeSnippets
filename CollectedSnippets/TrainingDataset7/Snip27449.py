def _test_invalid_generated_field_changes(self, db_persist):
        regular = models.IntegerField(default=1)
        generated_1 = models.GeneratedField(
            expression=F("pink") + F("pink"),
            output_field=models.IntegerField(),
            db_persist=db_persist,
        )
        generated_2 = models.GeneratedField(
            expression=F("pink") + F("pink") + F("pink"),
            output_field=models.IntegerField(),
            db_persist=db_persist,
        )
        tests = [
            ("test_igfc_1", regular, generated_1),
            ("test_igfc_2", generated_1, regular),
            ("test_igfc_3", generated_1, generated_2),
        ]
        if not connection.features.supports_alter_generated_column_data_type:
            generated_3 = models.GeneratedField(
                expression=F("pink") + F("pink"),
                output_field=models.DecimalField(decimal_places=2, max_digits=16),
                db_persist=db_persist,
            )
            tests.append(
                ("test_igfc_4", generated_1, generated_3),
            )
        for app_label, add_field, alter_field in tests:
            project_state = self.set_up_test_model(app_label)
            operations = [
                migrations.AddField("Pony", "modified_pink", add_field),
                migrations.AlterField("Pony", "modified_pink", alter_field),
            ]
            msg = (
                "Modifying GeneratedFields is not supported - the field "
                f"{app_label}.Pony.modified_pink must be removed and re-added with the "
                "new definition."
            )
            with self.assertRaisesMessage(ValueError, msg):
                self.apply_operations(app_label, project_state, operations)