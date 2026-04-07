def test_fields_immutability(self):
        """
        Rendering a model state doesn't alter its internal fields.
        """
        apps = Apps()
        field = models.CharField(max_length=1)
        state = ModelState("app", "Model", [("name", field)])
        Model = state.render(apps)
        self.assertNotEqual(Model._meta.get_field("name"), field)