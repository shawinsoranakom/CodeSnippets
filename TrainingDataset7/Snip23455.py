def test_get_min_num(self):
        class GetMinNumInline(GenericTabularInline):
            model = Media
            min_num = 5

            def get_min_num(self, request, obj):
                return 2

        modeladmin = admin.ModelAdmin(Episode, admin_site)
        modeladmin.inlines = [GetMinNumInline]
        e = self._create_object(Episode)
        request = self.factory.get(
            reverse("admin:generic_inline_admin_episode_change", args=(e.pk,))
        )
        request.user = User(username="super", is_superuser=True)
        response = modeladmin.changeform_view(request, object_id=str(e.pk))
        formset = response.context_data["inline_admin_formsets"][0].formset

        self.assertEqual(formset.min_num, 2)