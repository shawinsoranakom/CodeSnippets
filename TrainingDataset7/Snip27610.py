def test_custom_model_base(self):
        state = ModelState.from_model(ModelWithCustomBase)
        self.assertEqual(state.bases, (models.Model,))