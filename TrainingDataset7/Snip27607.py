def test_alter_field(self):
        project_state = self.get_base_project_state()
        self.assertEqual(
            list(project_state.relations["tests", "user"]),
            [("tests", "comment"), ("tests", "post")],
        )
        # Alter a foreign key to a non-relation field.
        project_state.alter_field(
            "tests",
            "comment",
            "user",
            models.IntegerField(),
            preserve_default=True,
        )
        self.assertEqual(
            list(project_state.relations["tests", "user"]),
            [("tests", "post")],
        )
        # Alter a non-relation field to a many-to-many field.
        m2m_field = models.ManyToManyField("tests.user")
        project_state.alter_field(
            "tests",
            "comment",
            "user",
            m2m_field,
            preserve_default=True,
        )
        self.assertEqual(
            list(project_state.relations["tests", "user"]),
            [("tests", "post"), ("tests", "comment")],
        )
        self.assertEqual(
            project_state.relations["tests", "user"]["tests", "comment"],
            {"user": m2m_field},
        )