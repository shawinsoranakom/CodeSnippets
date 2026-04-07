def test_alter_field_m2m_to_fk(self):
        project_state = self.get_base_project_state()
        project_state.add_model(
            ModelState(
                app_label="tests_other",
                name="user_other",
                fields=[("id", models.AutoField(primary_key=True))],
            )
        )
        self.assertEqual(
            list(project_state.relations["tests", "user"]),
            [("tests", "comment"), ("tests", "post")],
        )
        self.assertNotIn(("tests_other", "user_other"), project_state.relations)
        # Alter a many-to-many field to a foreign key.
        foreign_key = models.ForeignKey("tests_other.user_other", models.CASCADE)
        project_state.alter_field(
            "tests",
            "post",
            "authors",
            foreign_key,
            preserve_default=True,
        )
        self.assertEqual(
            list(project_state.relations["tests", "user"]),
            [("tests", "comment")],
        )
        self.assertEqual(
            list(project_state.relations["tests_other", "user_other"]),
            [("tests", "post")],
        )
        self.assertEqual(
            project_state.relations["tests_other", "user_other"]["tests", "post"],
            {"authors": foreign_key},
        )