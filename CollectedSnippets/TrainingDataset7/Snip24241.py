def test_defer_or_only_with_annotate(self):
        """
        Regression for #16409. Make sure defer() and only() work with
        annotate()
        """
        self.assertIsInstance(
            list(City.objects.annotate(Count("point")).defer("name")), list
        )
        self.assertIsInstance(
            list(City.objects.annotate(Count("point")).only("name")), list
        )