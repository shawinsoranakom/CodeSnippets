def test_remove_field(self):
        project_state = self.get_base_project_state()
        self.assertEqual(
            list(project_state.relations["tests", "user"]),
            [("tests", "comment"), ("tests", "post")],
        )
        # Remove a many-to-many field.
        project_state.remove_field("tests", "post", "authors")
        self.assertEqual(
            list(project_state.relations["tests", "user"]),
            [("tests", "comment")],
        )
        # Remove a foreign key.
        project_state.remove_field("tests", "comment", "user")
        self.assertEqual(project_state.relations["tests", "user"], {})