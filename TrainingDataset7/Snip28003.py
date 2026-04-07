def test_realistic_object(self):
        value = {
            "name": "John",
            "age": 20,
            "pets": [
                {"name": "Kit", "type": "cat", "age": 2},
                {"name": "Max", "type": "dog", "age": 1},
            ],
            "courses": [
                ["A1", "A2", "A3"],
                ["B1", "B2"],
                ["C1"],
            ],
        }
        obj = JSONModel.objects.create(value=value)
        obj.refresh_from_db()
        self.assertEqual(obj.value, value)