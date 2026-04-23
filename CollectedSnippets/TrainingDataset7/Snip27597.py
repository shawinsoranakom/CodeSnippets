def test_add_model_other_app(self):
        project_state = self.get_base_project_state()
        self.assertEqual(
            list(project_state.relations["tests", "user"]),
            [("tests", "comment"), ("tests", "post")],
        )
        project_state.add_model(
            ModelState(
                app_label="tests_other",
                name="comment",
                fields=[
                    ("id", models.AutoField(primary_key=True)),
                    ("user", models.ForeignKey("tests.user", models.CASCADE)),
                ],
            )
        )
        self.assertEqual(
            list(project_state.relations["tests", "user"]),
            [("tests", "comment"), ("tests", "post"), ("tests_other", "comment")],
        )