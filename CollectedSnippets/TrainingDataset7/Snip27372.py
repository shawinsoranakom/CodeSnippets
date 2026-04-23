def test_alter_field_reloads_state_on_fk_with_to_field_target_type_change(self):
        app_label = "test_alflrsfkwtflttc"
        project_state = self.apply_operations(
            app_label,
            ProjectState(),
            operations=[
                migrations.CreateModel(
                    "Rider",
                    fields=[
                        ("id", models.AutoField(primary_key=True)),
                        ("code", models.IntegerField(unique=True)),
                    ],
                ),
                migrations.CreateModel(
                    "Pony",
                    fields=[
                        ("id", models.AutoField(primary_key=True)),
                        (
                            "rider",
                            models.ForeignKey(
                                "%s.Rider" % app_label, models.CASCADE, to_field="code"
                            ),
                        ),
                    ],
                ),
            ],
        )
        operation = migrations.AlterField(
            "Rider",
            "code",
            models.CharField(max_length=100, unique=True),
        )
        self.apply_operations(app_label, project_state, operations=[operation])
        id_type, id_null = [
            (c.type_code, c.null_ok)
            for c in self.get_table_description("%s_rider" % app_label)
            if c.name == "code"
        ][0]
        fk_type, fk_null = [
            (c.type_code, c.null_ok)
            for c in self.get_table_description("%s_pony" % app_label)
            if c.name == "rider_id"
        ][0]
        self.assertEqual(id_type, fk_type)
        self.assertEqual(id_null, fk_null)