def test_equality(self):
        """
        == and != are implemented correctly.
        """
        # Test two things that should be equal
        project_state = ProjectState()
        project_state.add_model(
            ModelState(
                "migrations",
                "Tag",
                [
                    ("id", models.AutoField(primary_key=True)),
                    ("name", models.CharField(max_length=100)),
                    ("hidden", models.BooleanField()),
                ],
                {},
                None,
            )
        )
        project_state.apps  # Fill the apps cached property
        other_state = project_state.clone()
        self.assertEqual(project_state, project_state)
        self.assertEqual(project_state, other_state)
        self.assertIs(project_state != project_state, False)
        self.assertIs(project_state != other_state, False)
        self.assertNotEqual(project_state.apps, other_state.apps)

        # Make a very small change (max_len 99) and see if that affects it
        project_state = ProjectState()
        project_state.add_model(
            ModelState(
                "migrations",
                "Tag",
                [
                    ("id", models.AutoField(primary_key=True)),
                    ("name", models.CharField(max_length=99)),
                    ("hidden", models.BooleanField()),
                ],
                {},
                None,
            )
        )
        self.assertNotEqual(project_state, other_state)
        self.assertIs(project_state == other_state, False)