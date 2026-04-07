def test_add_field(self):
        project_state = self.get_base_project_state()
        self.assertNotIn(("tests", "post"), project_state.relations)
        # Add a self-referential foreign key.
        new_field = models.ForeignKey("self", models.CASCADE)
        project_state.add_field(
            "tests",
            "post",
            "next_post",
            new_field,
            preserve_default=True,
        )
        self.assertEqual(
            list(project_state.relations["tests", "post"]),
            [("tests", "post")],
        )
        self.assertEqual(
            project_state.relations["tests", "post"]["tests", "post"],
            {"next_post": new_field},
        )
        # Add a foreign key.
        new_field = models.ForeignKey("tests.post", models.CASCADE)
        project_state.add_field(
            "tests",
            "comment",
            "post",
            new_field,
            preserve_default=True,
        )
        self.assertEqual(
            list(project_state.relations["tests", "post"]),
            [("tests", "post"), ("tests", "comment")],
        )
        self.assertEqual(
            project_state.relations["tests", "post"]["tests", "comment"],
            {"post": new_field},
        )