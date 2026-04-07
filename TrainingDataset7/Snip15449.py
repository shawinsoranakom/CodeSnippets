def test_multi_choice_field_filter(self):
        modeladmin = DecadeFilterBookAdmin(Book, site)
        request = self.request_factory.get(
            "/",
            [("category__exact", "non-fiction"), ("category__exact", "fiction")],
        )
        request.user = self.alfred
        changelist = modeladmin.get_changelist_instance(request)
        queryset = changelist.get_queryset(request)
        self.assertSequenceEqual(
            queryset,
            list(
                Book.objects.filter(category__in=["non-fiction", "fiction"]).order_by(
                    "-id"
                )
            ),
        )
        filterspec = changelist.get_filters(request)[0][3]
        choices = list(filterspec.choices(changelist))
        expected_choice_values = [
            ("All", False, "?"),
            ("Non-Fictional", True, "?category__exact=non-fiction"),
            ("Fictional", True, "?category__exact=fiction"),
            ("We don't know", False, "?category__exact="),
            ("Not categorized", False, "?category__isnull=True"),
        ]
        for i, (display, selected, query_string) in enumerate(expected_choice_values):
            self.assertEqual(choices[i]["display"], display)
            self.assertIs(choices[i]["selected"], selected)
            self.assertEqual(choices[i]["query_string"], query_string)