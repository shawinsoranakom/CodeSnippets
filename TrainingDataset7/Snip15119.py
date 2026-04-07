def test_many_search_terms(self):
        parent = Parent.objects.create(name="Mary")
        Child.objects.create(parent=parent, name="Danielle")
        Child.objects.create(parent=parent, name="Daniel")

        m = ParentAdmin(Parent, custom_site)
        request = self.factory.get("/parent/", data={SEARCH_VAR: "daniel " * 80})
        request.user = self.superuser

        cl = m.get_changelist_instance(request)
        with CaptureQueriesContext(connection) as context:
            object_count = cl.queryset.count()
        self.assertEqual(object_count, 1)
        self.assertEqual(context.captured_queries[0]["sql"].count("JOIN"), 1)