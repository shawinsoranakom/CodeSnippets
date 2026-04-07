def test_get_select_related_custom_method(self):
        class GetListSelectRelatedAdmin(admin.ModelAdmin):
            list_display = ("band", "player")

            def get_list_select_related(self, request):
                return ("band", "player")

        ia = GetListSelectRelatedAdmin(Invitation, custom_site)
        request = self.factory.get("/invitation/")
        request.user = self.superuser
        cl = ia.get_changelist_instance(request)
        self.assertEqual(cl.queryset.query.select_related, {"player": {}, "band": {}})