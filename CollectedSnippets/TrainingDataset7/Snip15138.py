def test_distinct_for_non_unique_related_object_in_search_fields(self):
        """
        Regressions tests for #15819: If a field listed in search_fields
        is a non-unique related object, distinct() must be called.
        """
        parent = Parent.objects.create(name="Mary")
        Child.objects.create(parent=parent, name="Danielle")
        Child.objects.create(parent=parent, name="Daniel")

        m = ParentAdmin(Parent, custom_site)
        request = self.factory.get("/parent/", data={SEARCH_VAR: "daniel"})
        request.user = self.superuser

        cl = m.get_changelist_instance(request)
        # Make sure distinct() was called
        self.assertEqual(cl.queryset.count(), 1)
        # Queryset must be deletable.
        cl.queryset.delete()
        self.assertEqual(cl.queryset.count(), 0)