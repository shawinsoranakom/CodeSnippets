def test_complex_aggregations_require_kwarg(self):
        with self.assertRaisesMessage(
            TypeError, "Complex annotations require an alias"
        ):
            Author.objects.annotate(Sum(F("age") + F("friends__age")))
        with self.assertRaisesMessage(TypeError, "Complex aggregates require an alias"):
            Author.objects.aggregate(Sum("age") / Count("age"))
        with self.assertRaisesMessage(TypeError, "Complex aggregates require an alias"):
            Author.objects.aggregate(Sum(1))