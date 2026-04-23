def test_fields_ordering_equality(self):
        state = ModelState(
            "migrations",
            "Tag",
            [
                ("id", models.AutoField(primary_key=True)),
                ("name", models.CharField(max_length=100)),
                ("hidden", models.BooleanField()),
            ],
        )
        reordered_state = ModelState(
            "migrations",
            "Tag",
            [
                ("id", models.AutoField(primary_key=True)),
                # Purposely re-ordered.
                ("hidden", models.BooleanField()),
                ("name", models.CharField(max_length=100)),
            ],
        )
        self.assertEqual(state, reordered_state)