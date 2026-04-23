def test_distinct_for_non_unique_related_object_in_list_filter(self):
        """
        Regressions tests for #15819: If a field listed in list_filters
        is a non-unique related object, distinct() must be called.
        """
        parent = Parent.objects.create(name="Mary")
        # Two children with the same name
        Child.objects.create(parent=parent, name="Daniel")
        Child.objects.create(parent=parent, name="Daniel")

        m = ParentAdmin(Parent, custom_site)
        request = self.factory.get("/parent/", data={"child__name": "Daniel"})
        request.user = self.superuser

        cl = m.get_changelist_instance(request)
        # Make sure distinct() was called
        self.assertEqual(cl.queryset.count(), 1)
        # Queryset must be deletable.
        cl.queryset.delete()
        self.assertEqual(cl.queryset.count(), 0)