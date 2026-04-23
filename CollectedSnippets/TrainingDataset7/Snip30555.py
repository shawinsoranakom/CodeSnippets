def test_names_to_path_field(self):
        query = Query(None)
        query.add_annotation(Value(True), "value")
        path, final_field, targets, names = query.names_to_path(["value"], opts=None)
        self.assertEqual(path, [])
        self.assertIsInstance(final_field, BooleanField)
        self.assertEqual(len(targets), 1)
        self.assertIsInstance(targets[0], BooleanField)
        self.assertEqual(names, [])