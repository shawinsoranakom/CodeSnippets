def test_custom_lookup_none_rhs(self):
        """Lookup.can_use_none_as_rhs=True allows None as a lookup value."""
        season = Season.objects.create(year=2012, nulled_text_field=None)
        query = Season.objects.get_queryset().query
        field = query.model._meta.get_field("nulled_text_field")
        self.assertIsInstance(
            query.build_lookup(["isnull_none_rhs"], field, None), IsNullWithNoneAsRHS
        )
        self.assertTrue(
            Season.objects.filter(pk=season.pk, nulled_text_field__isnull_none_rhs=True)
        )