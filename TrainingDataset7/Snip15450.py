def test_multi_all_values_field_filter(self):
        modeladmin = DecadeFilterBookAdmin(Book, site)
        request = self.request_factory.get(
            "/",
            [
                ("author__email", "bob@example.com"),
                ("author__email", "lisa@example.com"),
            ],
        )
        request.user = self.alfred
        changelist = modeladmin.get_changelist_instance(request)
        queryset = changelist.get_queryset(request)
        self.assertSequenceEqual(
            queryset,
            list(
                Book.objects.filter(
                    author__email__in=["bob@example.com", "lisa@example.com"]
                ).order_by("-id")
            ),
        )
        filterspec = changelist.get_filters(request)[0][5]
        choices = list(filterspec.choices(changelist))
        expected_choice_values = [
            ("All", False, "?"),
            ("alfred@example.com", False, "?author__email=alfred%40example.com"),
            ("bob@example.com", True, "?author__email=bob%40example.com"),
            ("lisa@example.com", True, "?author__email=lisa%40example.com"),
        ]
        for i, (display, selected, query_string) in enumerate(expected_choice_values):
            self.assertEqual(choices[i]["display"], display)
            self.assertIs(choices[i]["selected"], selected)
            self.assertEqual(choices[i]["query_string"], query_string)