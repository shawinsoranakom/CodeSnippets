def test_get_max_num(self):
        class GetMaxNumInline(GenericTabularInline):
            model = Media
            extra = 5

            def get_max_num(self, request, obj):
                return 2

        modeladmin = admin.ModelAdmin(Episode, admin_site)
        modeladmin.inlines = [GetMaxNumInline]
        e = self._create_object(Episode)
        request = self.factory.get(
            reverse("admin:generic_inline_admin_episode_change", args=(e.pk,))
        )
        request.user = User(username="super", is_superuser=True)
        response = modeladmin.changeform_view(request, object_id=str(e.pk))
        formset = response.context_data["inline_admin_formsets"][0].formset

        self.assertEqual(formset.max_num, 2)