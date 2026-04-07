def test_rename_model_state_forwards(self):
        """
        RenameModel operations shouldn't trigger the caching of rendered apps
        on state without prior apps.
        """
        state = ProjectState()
        state.add_model(ModelState("migrations", "Foo", []))
        operation = migrations.RenameModel("Foo", "Bar")
        operation.state_forwards("migrations", state)
        self.assertNotIn("apps", state.__dict__)
        self.assertNotIn(("migrations", "foo"), state.models)
        self.assertIn(("migrations", "bar"), state.models)
        # Now with apps cached.
        apps = state.apps
        operation = migrations.RenameModel("Bar", "Foo")
        operation.state_forwards("migrations", state)
        self.assertIs(state.apps, apps)
        self.assertNotIn(("migrations", "bar"), state.models)
        self.assertIn(("migrations", "foo"), state.models)