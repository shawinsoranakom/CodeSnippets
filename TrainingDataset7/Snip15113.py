def test_specified_ordering_by_f_expression_without_asc_desc(self):
        class OrderedByFBandAdmin(admin.ModelAdmin):
            list_display = ["name", "genres", "nr_of_members"]
            ordering = (F("nr_of_members"), Upper("name"), F("genres"))

        m = OrderedByFBandAdmin(Band, custom_site)
        request = self.factory.get("/band/")
        request.user = self.superuser
        cl = m.get_changelist_instance(request)
        self.assertEqual(cl.get_ordering_field_columns(), {3: "asc", 2: "asc"})