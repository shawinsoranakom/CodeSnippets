def test_add_model(self):
        project_state = self.get_base_project_state()
        self.assertEqual(
            list(project_state.relations["tests", "user"]),
            [("tests", "comment"), ("tests", "post")],
        )
        self.assertEqual(
            list(project_state.relations["tests", "comment"]),
            [("tests", "comment")],
        )
        self.assertNotIn(("tests", "post"), project_state.relations)