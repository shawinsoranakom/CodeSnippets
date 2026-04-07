def test_runpython_manager_methods(self):
        def forwards(apps, schema_editor):
            UserModel = apps.get_model("auth", "User")
            user = UserModel.objects.create_user("user1", password="secure")
            self.assertIsInstance(user, UserModel)

        operation = migrations.RunPython(forwards, migrations.RunPython.noop)
        project_state = ProjectState()
        project_state.add_model(ModelState.from_model(User))
        project_state.add_model(ModelState.from_model(Group))
        project_state.add_model(ModelState.from_model(Permission))
        project_state.add_model(ModelState.from_model(ContentType))
        new_state = project_state.clone()
        with connection.schema_editor() as editor:
            operation.state_forwards("test_manager_methods", new_state)
            operation.database_forwards(
                "test_manager_methods",
                editor,
                project_state,
                new_state,
            )
        user = User.objects.get(username="user1")
        self.assertTrue(user.check_password("secure"))