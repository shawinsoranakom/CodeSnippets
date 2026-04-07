def test_relatedfieldlistfilter_foreignkey_default_ordering(self):
        """RelatedFieldListFilter ordering respects Model.ordering."""

        class BookAdmin(ModelAdmin):
            list_filter = ("employee",)

        self.addCleanup(setattr, Employee._meta, "ordering", Employee._meta.ordering)
        Employee._meta.ordering = ("name",)
        modeladmin = BookAdmin(Book, site)

        request = self.request_factory.get("/")
        request.user = self.alfred
        changelist = modeladmin.get_changelist_instance(request)
        filterspec = changelist.get_filters(request)[0][0]
        expected = [(self.jack.pk, "Jack Red"), (self.john.pk, "John Blue")]
        self.assertEqual(filterspec.lookup_choices, expected)