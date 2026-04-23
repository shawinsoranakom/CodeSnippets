def test_in_subquery(self):
        # This is a contrived test (and you really wouldn't write this query),
        # but it is a succinct way to test the __in=Subquery() construct.
        small_companies = Company.objects.filter(num_employees__lt=200).values("pk")
        subquery_test = Company.objects.filter(pk__in=Subquery(small_companies))
        self.assertCountEqual(subquery_test, [self.foobar_ltd, self.gmbh])
        subquery_test2 = Company.objects.filter(
            pk=Subquery(small_companies.filter(num_employees=3)[:1])
        )
        self.assertCountEqual(subquery_test2, [self.foobar_ltd])