def test_related_aggregate(self):
        vals = Author.objects.aggregate(Avg("friends__age"))
        self.assertEqual(vals, {"friends__age__avg": Approximate(34.07, places=2)})

        vals = Book.objects.filter(rating__lt=4.5).aggregate(Avg("authors__age"))
        self.assertEqual(vals, {"authors__age__avg": Approximate(38.2857, places=2)})

        vals = Author.objects.filter(name__contains="a").aggregate(Avg("book__rating"))
        self.assertEqual(vals, {"book__rating__avg": 4.0})

        vals = Book.objects.aggregate(Sum("publisher__num_awards"))
        self.assertEqual(vals, {"publisher__num_awards__sum": 30})

        vals = Publisher.objects.aggregate(Sum("book__price"))
        self.assertEqual(vals, {"book__price__sum": Decimal("270.27")})