def test_remove_relations(self):
        """
        #24225 - Relations between models are updated while
        remaining the relations and references for models of an old state.
        """
        new_apps = Apps()

        class A(models.Model):
            class Meta:
                app_label = "something"
                apps = new_apps

        class B(models.Model):
            to_a = models.ForeignKey(A, models.CASCADE)

            class Meta:
                app_label = "something"
                apps = new_apps

        def get_model_a(state):
            return [
                mod for mod in state.apps.get_models() if mod._meta.model_name == "a"
            ][0]

        project_state = ProjectState()
        project_state.add_model(ModelState.from_model(A))
        project_state.add_model(ModelState.from_model(B))
        self.assertEqual(len(get_model_a(project_state)._meta.related_objects), 1)
        old_state = project_state.clone()

        operation = RemoveField("b", "to_a")
        operation.state_forwards("something", project_state)
        # Model from old_state still has the relation
        model_a_old = get_model_a(old_state)
        model_a_new = get_model_a(project_state)
        self.assertIsNot(model_a_old, model_a_new)
        self.assertEqual(len(model_a_old._meta.related_objects), 1)
        self.assertEqual(len(model_a_new._meta.related_objects), 0)

        # Same test for deleted model
        project_state = ProjectState()
        project_state.add_model(ModelState.from_model(A))
        project_state.add_model(ModelState.from_model(B))
        old_state = project_state.clone()

        operation = DeleteModel("b")
        operation.state_forwards("something", project_state)
        model_a_old = get_model_a(old_state)
        model_a_new = get_model_a(project_state)
        self.assertIsNot(model_a_old, model_a_new)
        self.assertEqual(len(model_a_old._meta.related_objects), 1)
        self.assertEqual(len(model_a_new._meta.related_objects), 0)