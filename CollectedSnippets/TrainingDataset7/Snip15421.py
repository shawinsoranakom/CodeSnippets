def test_relatedonlyfieldlistfilter_foreignkey_reverse_relationships(self):
        class EmployeeAdminReverseRelationship(ModelAdmin):
            list_filter = (("book", RelatedOnlyFieldListFilter),)

        self.djangonaut_book.employee = self.john
        self.djangonaut_book.save()
        self.django_book.employee = self.jack
        self.django_book.save()

        modeladmin = EmployeeAdminReverseRelationship(Employee, site)
        request = self.request_factory.get("/")
        request.user = self.alfred
        changelist = modeladmin.get_changelist_instance(request)
        filterspec = changelist.get_filters(request)[0][0]
        self.assertCountEqual(
            filterspec.lookup_choices,
            [
                (self.djangonaut_book.pk, "Djangonaut: an art of living"),
                (self.bio_book.pk, "Django: a biography"),
                (self.django_book.pk, "The Django Book"),
            ],
        )