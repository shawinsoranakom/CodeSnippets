def test_choicesfieldlistfilter_has_none_choice(self):
        """
        The last choice is for the None value.
        """

        class BookmarkChoicesAdmin(ModelAdmin):
            list_display = ["none_or_null"]
            list_filter = ["none_or_null"]

        modeladmin = BookmarkChoicesAdmin(Bookmark, site)
        request = self.request_factory.get("/", {})
        request.user = self.alfred
        changelist = modeladmin.get_changelist_instance(request)
        filterspec = changelist.get_filters(request)[0][0]
        choices = list(filterspec.choices(changelist))
        self.assertEqual(choices[-1]["display"], "None")
        self.assertEqual(choices[-1]["query_string"], "?none_or_null__isnull=True")