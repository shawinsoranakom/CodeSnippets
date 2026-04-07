def test_get_extra(self):
        class GetExtraInline(GenericTabularInline):
            model = Media
            extra = 4

            def get_extra(self, request, obj):
                return 2

        modeladmin = admin.ModelAdmin(Episode, admin_site)
        modeladmin.inlines = [GetExtraInline]
        e = self._create_object(Episode)
        request = self.factory.get(
            reverse("admin:generic_inline_admin_episode_change", args=(e.pk,))
        )
        request.user = User(username="super", is_superuser=True)
        response = modeladmin.changeform_view(request, object_id=str(e.pk))
        formset = response.context_data["inline_admin_formsets"][0].formset

        self.assertEqual(formset.extra, 2)