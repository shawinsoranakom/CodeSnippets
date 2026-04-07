def test_remove_model(self):
        project_state = self.get_base_project_state()
        self.assertEqual(
            list(project_state.relations["tests", "user"]),
            [("tests", "comment"), ("tests", "post")],
        )
        self.assertEqual(
            list(project_state.relations["tests", "comment"]),
            [("tests", "comment")],
        )

        project_state.remove_model("tests", "comment")
        self.assertEqual(
            list(project_state.relations["tests", "user"]),
            [("tests", "post")],
        )
        self.assertNotIn(("tests", "comment"), project_state.relations)
        project_state.remove_model("tests", "post")
        self.assertEqual(project_state.relations, {})
        project_state.remove_model("tests", "user")
        self.assertEqual(project_state.relations, {})