def test_multi_related_field_filter(self):
        modeladmin = DecadeFilterBookAdmin(Book, site)
        request = self.request_factory.get(
            "/",
            [("author__id__exact", self.alfred.pk), ("author__id__exact", self.bob.pk)],
        )
        request.user = self.alfred
        changelist = modeladmin.get_changelist_instance(request)
        queryset = changelist.get_queryset(request)
        self.assertSequenceEqual(
            queryset,
            list(
                Book.objects.filter(
                    author__pk__in=[self.alfred.pk, self.bob.pk]
                ).order_by("-id")
            ),
        )
        filterspec = changelist.get_filters(request)[0][0]
        choices = list(filterspec.choices(changelist))
        expected_choice_values = [
            ("All", False, "?"),
            ("alfred", True, f"?author__id__exact={self.alfred.pk}"),
            ("bob", True, f"?author__id__exact={self.bob.pk}"),
            ("lisa", False, f"?author__id__exact={self.lisa.pk}"),
        ]
        for i, (display, selected, query_string) in enumerate(expected_choice_values):
            self.assertEqual(choices[i]["display"], display)
            self.assertIs(choices[i]["selected"], selected)
            self.assertEqual(choices[i]["query_string"], query_string)