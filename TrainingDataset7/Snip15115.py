def test_select_related_preserved_when_multi_valued_in_search_fields(self):
        parent = Parent.objects.create(name="Mary")
        Child.objects.create(parent=parent, name="Danielle")
        Child.objects.create(parent=parent, name="Daniel")

        m = ParentAdmin(Parent, custom_site)
        request = self.factory.get("/parent/", data={SEARCH_VAR: "daniel"})
        request.user = self.superuser

        cl = m.get_changelist_instance(request)
        self.assertEqual(cl.queryset.count(), 1)
        # select_related is preserved.
        self.assertEqual(cl.queryset.query.select_related, {"child": {}})