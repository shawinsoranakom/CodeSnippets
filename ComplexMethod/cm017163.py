def test_relation_spanning_filters(self):
        changelist_url = reverse("admin:admin_views_chapterxtra1_changelist")
        response = self.client.get(changelist_url)
        self.assertContains(
            response,
            '<search id="changelist-filter" '
            'aria-labelledby="changelist-filter-header">',
        )
        filters = {
            "chap__id__exact": {
                "values": [c.id for c in Chapter.objects.all()],
                "test": lambda obj, value: obj.chap.id == value,
            },
            "chap__title": {
                "values": [c.title for c in Chapter.objects.all()],
                "test": lambda obj, value: obj.chap.title == value,
            },
            "chap__book__id__exact": {
                "values": [b.id for b in Book.objects.all()],
                "test": lambda obj, value: obj.chap.book.id == value,
            },
            "chap__book__name": {
                "values": [b.name for b in Book.objects.all()],
                "test": lambda obj, value: obj.chap.book.name == value,
            },
            "chap__book__promo__id__exact": {
                "values": [p.id for p in Promo.objects.all()],
                "test": lambda obj, value: obj.chap.book.promo_set.filter(
                    id=value
                ).exists(),
            },
            "chap__book__promo__name": {
                "values": [p.name for p in Promo.objects.all()],
                "test": lambda obj, value: obj.chap.book.promo_set.filter(
                    name=value
                ).exists(),
            },
            # A forward relation (book) after a reverse relation (promo).
            "guest_author__promo__book__id__exact": {
                "values": [p.id for p in Book.objects.all()],
                "test": lambda obj, value: obj.guest_author.promo_set.filter(
                    book=value
                ).exists(),
            },
        }
        for filter_path, params in filters.items():
            for value in params["values"]:
                query_string = urlencode({filter_path: value})
                # ensure filter link exists
                self.assertContains(response, '<a href="?%s"' % query_string)
                # ensure link works
                filtered_response = self.client.get(
                    "%s?%s" % (changelist_url, query_string)
                )
                self.assertEqual(filtered_response.status_code, 200)
                # ensure changelist contains only valid objects
                for obj in filtered_response.context["cl"].queryset.all():
                    self.assertTrue(params["test"](obj, value))