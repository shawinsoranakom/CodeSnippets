def test_exact_lookup_with_invalid_value(self):
        Child.objects.create(name="Test", age=10)
        m = admin.ModelAdmin(Child, custom_site)
        m.search_fields = ["pk__exact"]

        request = self.factory.get("/", data={SEARCH_VAR: "foo"})
        request.user = self.superuser

        # Invalid values are gracefully ignored.
        cl = m.get_changelist_instance(request)
        self.assertCountEqual(cl.queryset, [])