def test_filter_aggregate(self):
        vals = Author.objects.filter(age__gt=29).aggregate(Sum("age"))
        self.assertEqual(vals, {"age__sum": 254})