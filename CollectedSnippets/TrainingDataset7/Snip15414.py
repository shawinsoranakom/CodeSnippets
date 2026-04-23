def test_relatedfieldlistfilter_foreignkey_ordering(self):
        """RelatedFieldListFilter ordering respects ModelAdmin.ordering."""

        class EmployeeAdminWithOrdering(ModelAdmin):
            ordering = ("name",)

        class BookAdmin(ModelAdmin):
            list_filter = ("employee",)

        site.register(Employee, EmployeeAdminWithOrdering)
        self.addCleanup(lambda: site.unregister(Employee))
        modeladmin = BookAdmin(Book, site)

        request = self.request_factory.get("/")
        request.user = self.alfred
        changelist = modeladmin.get_changelist_instance(request)
        filterspec = changelist.get_filters(request)[0][0]
        expected = [(self.jack.pk, "Jack Red"), (self.john.pk, "John Blue")]
        self.assertEqual(filterspec.lookup_choices, expected)