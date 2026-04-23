def test_aliases_quoted(self):
        # Aliases are quoted to protected aliases that might be reserved names
        vals = Book.objects.aggregate(number=Max("pages"), select=Max("pages"))
        self.assertEqual(vals, {"number": 1132, "select": 1132})