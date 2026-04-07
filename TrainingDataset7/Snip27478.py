def test_formatted_description_no_category(self):
        operation = Operation()
        self.assertEqual(operation.formatted_description(), "? Operation: ((), {})")