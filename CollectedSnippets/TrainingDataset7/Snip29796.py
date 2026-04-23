def test_roundtrip_with_null(self):
        for field_value in [
            {"a": "b", "c": None},
            {"Енеїда": "Ти знаєш, він який суціга", "Зефір": None},
        ]:
            with self.subTest(field_value=field_value):
                instance = HStoreModel(field=field_value)
                data = serializers.serialize("json", [instance])
                new_instance = list(serializers.deserialize("json", data))[0].object
                self.assertEqual(instance.field, new_instance.field)