def test_related_objects(self):
        result_key = "get_all_related_objects_with_model"
        for model, expected in TEST_RESULTS[result_key].items():
            objects = [
                (field, self._model(model, field))
                for field in model._meta.get_fields()
                if field.auto_created and not field.concrete
            ]
            self.assertEqual(
                sorted(self._map_related_query_names(objects), key=self.key_name),
                sorted(expected, key=self.key_name),
            )