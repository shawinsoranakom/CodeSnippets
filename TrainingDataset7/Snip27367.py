def test_alter_field_pk_fk(self):
        """
        Tests the AlterField operation on primary keys changes any FKs pointing
        to it.
        """
        project_state = self.set_up_test_model("test_alflpkfk", related_model=True)
        project_state = self.apply_operations(
            "test_alflpkfk",
            project_state,
            [
                migrations.CreateModel(
                    "Stable",
                    fields=[
                        ("ponies", models.ManyToManyField("Pony")),
                    ],
                ),
                migrations.AddField(
                    "Pony",
                    "stables",
                    models.ManyToManyField("Stable"),
                ),
            ],
        )
        # Test the state alteration
        operation = migrations.AlterField(
            "Pony", "id", models.FloatField(primary_key=True)
        )
        new_state = project_state.clone()
        operation.state_forwards("test_alflpkfk", new_state)
        self.assertIsInstance(
            project_state.models["test_alflpkfk", "pony"].fields["id"],
            models.AutoField,
        )
        self.assertIsInstance(
            new_state.models["test_alflpkfk", "pony"].fields["id"],
            models.FloatField,
        )

        def assertIdTypeEqualsFkType():
            with connection.cursor() as cursor:
                id_type, id_null = [
                    (c.type_code, c.null_ok)
                    for c in connection.introspection.get_table_description(
                        cursor, "test_alflpkfk_pony"
                    )
                    if c.name == "id"
                ][0]
                fk_type, fk_null = [
                    (c.type_code, c.null_ok)
                    for c in connection.introspection.get_table_description(
                        cursor, "test_alflpkfk_rider"
                    )
                    if c.name == "pony_id"
                ][0]
                m2m_fk_type, m2m_fk_null = [
                    (c.type_code, c.null_ok)
                    for c in connection.introspection.get_table_description(
                        cursor,
                        "test_alflpkfk_pony_stables",
                    )
                    if c.name == "pony_id"
                ][0]
                remote_m2m_fk_type, remote_m2m_fk_null = [
                    (c.type_code, c.null_ok)
                    for c in connection.introspection.get_table_description(
                        cursor,
                        "test_alflpkfk_stable_ponies",
                    )
                    if c.name == "pony_id"
                ][0]
            self.assertEqual(id_type, fk_type)
            self.assertEqual(id_type, m2m_fk_type)
            self.assertEqual(id_type, remote_m2m_fk_type)
            self.assertEqual(id_null, fk_null)
            self.assertEqual(id_null, m2m_fk_null)
            self.assertEqual(id_null, remote_m2m_fk_null)

        assertIdTypeEqualsFkType()
        # Test the database alteration
        with connection.schema_editor() as editor:
            operation.database_forwards(
                "test_alflpkfk", editor, project_state, new_state
            )
        assertIdTypeEqualsFkType()
        if connection.features.supports_foreign_keys:
            self.assertFKExists(
                "test_alflpkfk_pony_stables",
                ["pony_id"],
                ("test_alflpkfk_pony", "id"),
            )
            self.assertFKExists(
                "test_alflpkfk_stable_ponies",
                ["pony_id"],
                ("test_alflpkfk_pony", "id"),
            )
        # And test reversal
        with connection.schema_editor() as editor:
            operation.database_backwards(
                "test_alflpkfk", editor, new_state, project_state
            )
        assertIdTypeEqualsFkType()
        if connection.features.supports_foreign_keys:
            self.assertFKExists(
                "test_alflpkfk_pony_stables",
                ["pony_id"],
                ("test_alflpkfk_pony", "id"),
            )
            self.assertFKExists(
                "test_alflpkfk_stable_ponies",
                ["pony_id"],
                ("test_alflpkfk_pony", "id"),
            )