def test_relatedfieldlistfilter_reverse_relationships_default_ordering(self):
        self.addCleanup(setattr, Book._meta, "ordering", Book._meta.ordering)
        Book._meta.ordering = ("title",)
        modeladmin = CustomUserAdmin(User, site)

        request = self.request_factory.get("/")
        request.user = self.alfred
        changelist = modeladmin.get_changelist_instance(request)
        filterspec = changelist.get_filters(request)[0][0]
        expected = [
            (self.bio_book.pk, "Django: a biography"),
            (self.djangonaut_book.pk, "Djangonaut: an art of living"),
            (self.guitar_book.pk, "Guitar for dummies"),
            (self.django_book.pk, "The Django Book"),
        ]
        self.assertEqual(filterspec.lookup_choices, expected)