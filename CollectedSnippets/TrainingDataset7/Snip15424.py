def test_relatedonlyfieldlistfilter_foreignkey_default_ordering(self):
        """RelatedOnlyFieldListFilter ordering respects Meta.ordering."""

        class BookAdmin(ModelAdmin):
            list_filter = (("employee", RelatedOnlyFieldListFilter),)

        albert = Employee.objects.create(name="Albert Green", department=self.dev)
        self.djangonaut_book.employee = albert
        self.djangonaut_book.save()
        self.bio_book.employee = self.jack
        self.bio_book.save()

        self.addCleanup(setattr, Employee._meta, "ordering", Employee._meta.ordering)
        Employee._meta.ordering = ("name",)
        modeladmin = BookAdmin(Book, site)

        request = self.request_factory.get("/")
        request.user = self.alfred
        changelist = modeladmin.get_changelist_instance(request)
        filterspec = changelist.get_filters(request)[0][0]
        expected = [(albert.pk, "Albert Green"), (self.jack.pk, "Jack Red")]
        self.assertEqual(filterspec.lookup_choices, expected)