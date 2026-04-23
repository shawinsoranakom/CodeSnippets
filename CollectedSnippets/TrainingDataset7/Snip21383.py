def test_subquery_references_joined_table_twice(self):
        inner = Company.objects.filter(
            num_chairs__gte=OuterRef("ceo__salary"),
            num_employees__gte=OuterRef("point_of_contact__salary"),
        )
        # Another contrived example (there is no need to have a subquery here)
        outer = Company.objects.filter(pk__in=Subquery(inner.values("pk")))
        self.assertFalse(outer.exists())