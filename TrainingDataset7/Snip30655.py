def test_combine_or_filter_reuse(self):
        combined = Author.objects.filter(name="a1") | Author.objects.filter(name="a3")
        self.assertEqual(combined.get(name="a1"), self.a1)