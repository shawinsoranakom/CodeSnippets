def test_relatedonlyfieldlistfilter_manytomany_reverse_relationships(self):
        class UserAdminReverseRelationship(ModelAdmin):
            list_filter = (("books_contributed", RelatedOnlyFieldListFilter),)

        modeladmin = UserAdminReverseRelationship(User, site)
        request = self.request_factory.get("/")
        request.user = self.alfred
        changelist = modeladmin.get_changelist_instance(request)
        filterspec = changelist.get_filters(request)[0][0]
        self.assertEqual(
            filterspec.lookup_choices,
            [(self.guitar_book.pk, "Guitar for dummies")],
        )