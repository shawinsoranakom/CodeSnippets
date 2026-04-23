def test_multiple_search_fields(self):
        """
        All rows containing each of the searched words are returned, where each
        word must be in one of search_fields.
        """
        band_duo = Group.objects.create(name="Duo")
        band_hype = Group.objects.create(name="The Hype")
        mary = Musician.objects.create(name="Mary Halvorson")
        jonathan = Musician.objects.create(name="Jonathan Finlayson")
        band_duo.members.set([mary, jonathan])
        Concert.objects.create(name="Tiny desk concert", group=band_duo)
        Concert.objects.create(name="Woodstock concert", group=band_hype)
        # FK lookup.
        concert_model_admin = ConcertAdmin(Concert, custom_site)
        concert_model_admin.search_fields = ["group__name", "name"]
        # Reverse FK lookup.
        group_model_admin = GroupAdmin(Group, custom_site)
        group_model_admin.search_fields = ["name", "concert__name", "members__name"]
        for search_string, result_count in (
            ("Duo Concert", 1),
            ("Tiny Desk Concert", 1),
            ("Concert", 2),
            ("Other Concert", 0),
            ("Duo Woodstock", 0),
        ):
            with self.subTest(search_string=search_string):
                # FK lookup.
                request = self.factory.get(
                    "/concert/", data={SEARCH_VAR: search_string}
                )
                request.user = self.superuser
                concert_changelist = concert_model_admin.get_changelist_instance(
                    request
                )
                self.assertEqual(concert_changelist.queryset.count(), result_count)
                # Reverse FK lookup.
                request = self.factory.get("/group/", data={SEARCH_VAR: search_string})
                request.user = self.superuser
                group_changelist = group_model_admin.get_changelist_instance(request)
                self.assertEqual(group_changelist.queryset.count(), result_count)
        # Many-to-many lookup.
        for search_string, result_count in (
            ("Finlayson Duo Tiny", 1),
            ("Finlayson", 1),
            ("Finlayson Hype", 0),
            ("Jonathan Finlayson Duo", 1),
            ("Mary Jonathan Duo", 0),
            ("Oscar Finlayson Duo", 0),
        ):
            with self.subTest(search_string=search_string):
                request = self.factory.get("/group/", data={SEARCH_VAR: search_string})
                request.user = self.superuser
                group_changelist = group_model_admin.get_changelist_instance(request)
                self.assertEqual(group_changelist.queryset.count(), result_count)