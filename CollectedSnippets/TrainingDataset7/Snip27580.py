def test_self_relation(self):
        """
        #24513 - Modifying an object pointing to itself would cause it to be
        rendered twice and thus breaking its related M2M through objects.
        """

        class A(models.Model):
            to_a = models.ManyToManyField("something.A", symmetrical=False)

            class Meta:
                app_label = "something"

        def get_model_a(state):
            return [
                mod for mod in state.apps.get_models() if mod._meta.model_name == "a"
            ][0]

        project_state = ProjectState()
        project_state.add_model(ModelState.from_model(A))
        self.assertEqual(len(get_model_a(project_state)._meta.related_objects), 1)
        old_state = project_state.clone()

        operation = AlterField(
            model_name="a",
            name="to_a",
            field=models.ManyToManyField("something.A", symmetrical=False, blank=True),
        )
        # At this point the model would be rendered twice causing its related
        # M2M through objects to point to an old copy and thus breaking their
        # attribute lookup.
        operation.state_forwards("something", project_state)

        model_a_old = get_model_a(old_state)
        model_a_new = get_model_a(project_state)
        self.assertIsNot(model_a_old, model_a_new)

        # The old model's _meta is still consistent
        field_to_a_old = model_a_old._meta.get_field("to_a")
        self.assertEqual(field_to_a_old.m2m_field_name(), "from_a")
        self.assertEqual(field_to_a_old.m2m_reverse_field_name(), "to_a")
        self.assertIs(field_to_a_old.related_model, model_a_old)
        self.assertIs(
            field_to_a_old.remote_field.through._meta.get_field("to_a").related_model,
            model_a_old,
        )
        self.assertIs(
            field_to_a_old.remote_field.through._meta.get_field("from_a").related_model,
            model_a_old,
        )

        # The new model's _meta is still consistent
        field_to_a_new = model_a_new._meta.get_field("to_a")
        self.assertEqual(field_to_a_new.m2m_field_name(), "from_a")
        self.assertEqual(field_to_a_new.m2m_reverse_field_name(), "to_a")
        self.assertIs(field_to_a_new.related_model, model_a_new)
        self.assertIs(
            field_to_a_new.remote_field.through._meta.get_field("to_a").related_model,
            model_a_new,
        )
        self.assertIs(
            field_to_a_new.remote_field.through._meta.get_field("from_a").related_model,
            model_a_new,
        )