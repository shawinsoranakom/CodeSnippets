def test_relations_population(self):
        tests = [
            (
                "add_model",
                [
                    ModelState(
                        app_label="migrations",
                        name="Tag",
                        fields=[("id", models.AutoField(primary_key=True))],
                    ),
                ],
            ),
            ("remove_model", ["tests", "comment"]),
            ("rename_model", ["tests", "comment", "opinion"]),
            (
                "add_field",
                [
                    "tests",
                    "post",
                    "next_post",
                    models.ForeignKey("self", models.CASCADE),
                    True,
                ],
            ),
            ("remove_field", ["tests", "post", "text"]),
            ("rename_field", ["tests", "comment", "user", "author"]),
            (
                "alter_field",
                [
                    "tests",
                    "comment",
                    "user",
                    models.IntegerField(),
                    True,
                ],
            ),
        ]
        for method, args in tests:
            with self.subTest(method=method):
                project_state = self.get_base_project_state()
                getattr(project_state, method)(*args)
                # ProjectState's `_relations` are populated on `relations`
                # access.
                self.assertIsNone(project_state._relations)
                self.assertEqual(project_state.relations, project_state._relations)
                self.assertIsNotNone(project_state._relations)