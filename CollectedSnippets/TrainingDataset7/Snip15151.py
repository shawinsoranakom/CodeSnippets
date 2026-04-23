def test_search_with_exact_lookup_relationship_field(self):
        child = Child.objects.create(name="I am a child", age=11)
        grandchild = GrandChild.objects.create(name="I am a grandchild", parent=child)
        model_admin = GrandChildAdmin(GrandChild, custom_site)

        request = self.factory.get("/", data={SEARCH_VAR: "'I am a child'"})
        request.user = self.superuser
        cl = model_admin.get_changelist_instance(request)
        self.assertCountEqual(cl.queryset, [grandchild])
        for search_term, expected_result in [
            ("11", [grandchild]),
            ("'I am a child'", [grandchild]),
            ("1", []),
            ("A", []),
            ("random", []),
        ]:
            request = self.factory.get("/", data={SEARCH_VAR: search_term})
            request.user = self.superuser
            with self.subTest(search_term=search_term):
                cl = model_admin.get_changelist_instance(request)
                self.assertCountEqual(cl.queryset, expected_result)