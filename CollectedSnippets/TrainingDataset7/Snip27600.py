def test_rename_model_no_relations(self):
        project_state = self.get_base_project_state()
        self.assertEqual(
            list(project_state.relations["tests", "user"]),
            [("tests", "comment"), ("tests", "post")],
        )
        related_field = project_state.relations["tests", "user"]["tests", "post"]
        self.assertNotIn(("tests", "post"), project_state.relations)
        # Rename a model without relations.
        project_state.rename_model("tests", "post", "blog")
        self.assertEqual(
            list(project_state.relations["tests", "user"]),
            [("tests", "comment"), ("tests", "blog")],
        )
        self.assertNotIn(("tests", "blog"), project_state.relations)
        self.assertEqual(
            related_field,
            project_state.relations["tests", "user"]["tests", "blog"],
        )