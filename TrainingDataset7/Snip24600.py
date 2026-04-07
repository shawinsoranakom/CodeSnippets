def test_deconstruct_empty(self):
        field = GeometryField()
        *_, kwargs = field.deconstruct()
        self.assertEqual(kwargs, {"srid": 4326})