def test_add_field_m2m_with_through(self):
        project_state = self.get_base_project_state()
        project_state.add_model(
            ModelState(
                app_label="tests",
                name="Tag",
                fields=[("id", models.AutoField(primary_key=True))],
            )
        )
        project_state.add_model(
            ModelState(
                app_label="tests",
                name="PostTag",
                fields=[
                    ("id", models.AutoField(primary_key=True)),
                    ("post", models.ForeignKey("tests.post", models.CASCADE)),
                    ("tag", models.ForeignKey("tests.tag", models.CASCADE)),
                ],
            )
        )
        self.assertEqual(
            list(project_state.relations["tests", "post"]),
            [("tests", "posttag")],
        )
        self.assertEqual(
            list(project_state.relations["tests", "tag"]),
            [("tests", "posttag")],
        )
        # Add a many-to-many field with the through model.
        new_field = models.ManyToManyField("tests.tag", through="tests.posttag")
        project_state.add_field(
            "tests",
            "post",
            "tags",
            new_field,
            preserve_default=True,
        )
        self.assertEqual(
            list(project_state.relations["tests", "post"]),
            [("tests", "posttag")],
        )
        self.assertEqual(
            list(project_state.relations["tests", "tag"]),
            [("tests", "posttag"), ("tests", "post")],
        )
        self.assertEqual(
            project_state.relations["tests", "tag"]["tests", "post"],
            {"tags": new_field},
        )