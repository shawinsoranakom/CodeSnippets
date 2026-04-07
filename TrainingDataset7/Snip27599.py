def test_rename_model(self):
        project_state = self.get_base_project_state()
        self.assertEqual(
            list(project_state.relations["tests", "user"]),
            [("tests", "comment"), ("tests", "post")],
        )
        self.assertEqual(
            list(project_state.relations["tests", "comment"]),
            [("tests", "comment")],
        )

        related_field = project_state.relations["tests", "user"]["tests", "comment"]
        project_state.rename_model("tests", "comment", "opinion")
        self.assertEqual(
            list(project_state.relations["tests", "user"]),
            [("tests", "post"), ("tests", "opinion")],
        )
        self.assertEqual(
            list(project_state.relations["tests", "opinion"]),
            [("tests", "opinion")],
        )
        self.assertNotIn(("tests", "comment"), project_state.relations)
        self.assertEqual(
            project_state.relations["tests", "user"]["tests", "opinion"],
            related_field,
        )

        project_state.rename_model("tests", "user", "author")
        self.assertEqual(
            list(project_state.relations["tests", "author"]),
            [("tests", "post"), ("tests", "opinion")],
        )
        self.assertNotIn(("tests", "user"), project_state.relations)