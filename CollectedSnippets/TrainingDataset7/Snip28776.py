def test_many_to_many_with_model(self):
        for model, expected_result in TEST_RESULTS["many_to_many_with_model"].items():
            models = [self._model(model, field) for field in model._meta.many_to_many]
            self.assertEqual(models, expected_result)