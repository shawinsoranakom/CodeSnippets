def test_deepcopy_and_circular_references(self):
        # Regression for #12876 -- Model methods that include queries that
        # recursive don't cause recursion depth problems under deepcopy.
        self.r.cached_query = Article.objects.filter(reporter=self.r)
        self.assertEqual(repr(deepcopy(self.r)), "<Reporter: John Smith>")