def test_exact_lookup_mixed_terms(self):
        """
        Multi-term search validates each term independently.

        For 'foo 123' with search_fields=['name__icontains', 'age__exact']:
        - 'foo': age lookup skipped (invalid), name lookup used
        - '123': both lookups used (valid for age)
        No Cast should be used; invalid lookups are simply skipped.
        """
        child = Child.objects.create(name="foo123", age=123)
        Child.objects.create(name="other", age=456)
        m = admin.ModelAdmin(Child, custom_site)
        m.search_fields = ["name__icontains", "age__exact"]

        request = self.factory.get("/", data={SEARCH_VAR: "foo 123"})
        request.user = self.superuser

        # One result matching on foo and 123.
        cl = m.get_changelist_instance(request)
        self.assertCountEqual(cl.queryset, [child])

        # "xyz" - invalid for age (skipped), no match for name either.
        request = self.factory.get("/", data={SEARCH_VAR: "xyz"})
        request.user = self.superuser
        cl = m.get_changelist_instance(request)
        self.assertCountEqual(cl.queryset, [])