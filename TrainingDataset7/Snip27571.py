def test_render(self):
        """
        Tests rendering a ProjectState into an Apps.
        """
        project_state = ProjectState()
        project_state.add_model(
            ModelState(
                app_label="migrations",
                name="Tag",
                fields=[
                    ("id", models.AutoField(primary_key=True)),
                    ("name", models.CharField(max_length=100)),
                    ("hidden", models.BooleanField()),
                ],
            )
        )
        project_state.add_model(
            ModelState(
                app_label="migrations",
                name="SubTag",
                fields=[
                    (
                        "tag_ptr",
                        models.OneToOneField(
                            "migrations.Tag",
                            models.CASCADE,
                            auto_created=True,
                            parent_link=True,
                            primary_key=True,
                            to_field="id",
                            serialize=False,
                        ),
                    ),
                    ("awesome", models.BooleanField()),
                ],
                bases=("migrations.Tag",),
            )
        )

        base_mgr = models.Manager()
        mgr1 = FoodManager("a", "b")
        mgr2 = FoodManager("x", "y", c=3, d=4)
        project_state.add_model(
            ModelState(
                app_label="migrations",
                name="Food",
                fields=[
                    ("id", models.AutoField(primary_key=True)),
                ],
                managers=[
                    # The ordering we really want is objects, mgr1, mgr2
                    ("default", base_mgr),
                    ("food_mgr2", mgr2),
                    ("food_mgr1", mgr1),
                ],
            )
        )

        new_apps = project_state.apps
        self.assertEqual(
            new_apps.get_model("migrations", "Tag")._meta.get_field("name").max_length,
            100,
        )
        self.assertIs(
            new_apps.get_model("migrations", "Tag")._meta.get_field("hidden").null,
            False,
        )

        self.assertEqual(
            len(new_apps.get_model("migrations", "SubTag")._meta.local_fields), 2
        )

        Food = new_apps.get_model("migrations", "Food")
        self.assertEqual(
            [mgr.name for mgr in Food._meta.managers],
            ["default", "food_mgr1", "food_mgr2"],
        )
        self.assertTrue(all(isinstance(mgr.name, str) for mgr in Food._meta.managers))
        self.assertEqual(
            [mgr.__class__ for mgr in Food._meta.managers],
            [models.Manager, FoodManager, FoodManager],
        )