def test_exact_lookup_with_more_lenient_formfield(self):
        """
        Exact lookups on BooleanField use formfield().to_python() for lenient
        parsing. Using model field's to_python() would reject 'false' whereas
        the form field accepts it.
        """
        obj = UnorderedObject.objects.create(bool=False)
        UnorderedObject.objects.create(bool=True)
        m = admin.ModelAdmin(UnorderedObject, custom_site)
        m.search_fields = ["bool__exact"]

        # 'false' is accepted by form field but rejected by model field.
        request = self.factory.get("/", data={SEARCH_VAR: "false"})
        request.user = self.superuser

        cl = m.get_changelist_instance(request)
        self.assertCountEqual(cl.queryset, [obj])