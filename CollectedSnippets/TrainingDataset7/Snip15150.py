def test_search_with_exact_lookup_for_non_string_field(self):
        child = Child.objects.create(name="Asher", age=11)
        model_admin = ChildAdmin(Child, custom_site)

        for search_term, expected_result in [
            ("11", [child]),
            ("Asher", [child]),
            ("1", []),
            ("A", []),
            ("random", []),
        ]:
            request = self.factory.get("/", data={SEARCH_VAR: search_term})
            request.user = self.superuser
            with self.subTest(search_term=search_term):
                # 1 query for filtered result, 1 for filtered count, 1 for
                # total count.
                with self.assertNumQueries(3):
                    cl = model_admin.get_changelist_instance(request)
                self.assertCountEqual(cl.queryset, expected_result)