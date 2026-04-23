def test_lookup_allowed_considers_dynamic_list_filter(self):
        class ConcertAdmin(ModelAdmin):
            list_filter = ["main_band__sign_date"]

            def get_list_filter(self, request):
                if getattr(request, "user", None):
                    return self.list_filter + ["main_band__name"]
                return self.list_filter

        model_admin = ConcertAdmin(Concert, self.site)
        request_band_name_filter = RequestFactory().get(
            "/", {"main_band__name": "test"}
        )
        self.assertIs(
            model_admin.lookup_allowed(
                "main_band__sign_date", "?", request_band_name_filter
            ),
            True,
        )
        self.assertIs(
            model_admin.lookup_allowed(
                "main_band__name", "?", request_band_name_filter
            ),
            False,
        )
        request_with_superuser = request
        self.assertIs(
            model_admin.lookup_allowed(
                "main_band__sign_date", "?", request_with_superuser
            ),
            True,
        )
        self.assertIs(
            model_admin.lookup_allowed("main_band__name", "?", request_with_superuser),
            True,
        )