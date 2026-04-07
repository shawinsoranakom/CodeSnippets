def test_add_relations(self):
        """
        #24573 - Adding relations to existing models should reload the
        referenced models too.
        """
        new_apps = Apps()

        class A(models.Model):
            class Meta:
                app_label = "something"
                apps = new_apps

        class B(A):
            class Meta:
                app_label = "something"
                apps = new_apps

        class C(models.Model):
            class Meta:
                app_label = "something"
                apps = new_apps

        project_state = ProjectState()
        project_state.add_model(ModelState.from_model(A))
        project_state.add_model(ModelState.from_model(B))
        project_state.add_model(ModelState.from_model(C))

        project_state.apps  # We need to work with rendered models

        old_state = project_state.clone()
        model_a_old = old_state.apps.get_model("something", "A")
        model_b_old = old_state.apps.get_model("something", "B")
        model_c_old = old_state.apps.get_model("something", "C")
        # The relations between the old models are correct
        self.assertIs(model_a_old._meta.get_field("b").related_model, model_b_old)
        self.assertIs(model_b_old._meta.get_field("a_ptr").related_model, model_a_old)

        operation = AddField(
            "c",
            "to_a",
            models.OneToOneField(
                "something.A",
                models.CASCADE,
                related_name="from_c",
            ),
        )
        operation.state_forwards("something", project_state)
        model_a_new = project_state.apps.get_model("something", "A")
        model_b_new = project_state.apps.get_model("something", "B")
        model_c_new = project_state.apps.get_model("something", "C")

        # All models have changed
        self.assertIsNot(model_a_old, model_a_new)
        self.assertIsNot(model_b_old, model_b_new)
        self.assertIsNot(model_c_old, model_c_new)
        # The relations between the old models still hold
        self.assertIs(model_a_old._meta.get_field("b").related_model, model_b_old)
        self.assertIs(model_b_old._meta.get_field("a_ptr").related_model, model_a_old)
        # The relations between the new models correct
        self.assertIs(model_a_new._meta.get_field("b").related_model, model_b_new)
        self.assertIs(model_b_new._meta.get_field("a_ptr").related_model, model_a_new)
        self.assertIs(model_a_new._meta.get_field("from_c").related_model, model_c_new)
        self.assertIs(model_c_new._meta.get_field("to_a").related_model, model_a_new)