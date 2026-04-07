def test_empty_aggregate(self):
        self.assertEqual(Author.objects.aggregate(), {})