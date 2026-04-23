def test_count(self):
        vals = Book.objects.aggregate(Count("rating"))
        self.assertEqual(vals, {"rating__count": 6})