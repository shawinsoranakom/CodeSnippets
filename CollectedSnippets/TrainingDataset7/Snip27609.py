def test_many_relations_to_same_model(self):
        project_state = self.get_base_project_state()
        new_field = models.ForeignKey("tests.user", models.CASCADE)
        project_state.add_field(
            "tests",
            "comment",
            "reviewer",
            new_field,
            preserve_default=True,
        )
        self.assertEqual(
            list(project_state.relations["tests", "user"]),
            [("tests", "comment"), ("tests", "post")],
        )
        comment_rels = project_state.relations["tests", "user"]["tests", "comment"]
        # Two foreign keys to the same model.
        self.assertEqual(len(comment_rels), 2)
        self.assertEqual(comment_rels["reviewer"], new_field)
        # Rename the second foreign key.
        project_state.rename_field("tests", "comment", "reviewer", "supervisor")
        self.assertEqual(len(comment_rels), 2)
        self.assertEqual(comment_rels["supervisor"], new_field)
        # Remove the first foreign key.
        project_state.remove_field("tests", "comment", "user")
        self.assertEqual(comment_rels, {"supervisor": new_field})