def test_values_subquery(self):
        self.assertCountEqual(
            Number.objects.filter(pk__in=Number.objects.none().values("pk")), []
        )
        self.assertCountEqual(
            Number.objects.filter(pk__in=Number.objects.none().values_list("pk")), []
        )