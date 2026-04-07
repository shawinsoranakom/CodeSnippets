def test_extra_param(self):
        """
        With extra=0, there should be one form.
        """

        class ExtraInline(GenericTabularInline):
            model = Media
            extra = 0

        modeladmin = admin.ModelAdmin(Episode, admin_site)
        modeladmin.inlines = [ExtraInline]

        e = self._create_object(Episode)
        request = self.factory.get(
            reverse("admin:generic_inline_admin_episode_change", args=(e.pk,))
        )
        request.user = User(username="super", is_superuser=True)
        response = modeladmin.changeform_view(request, object_id=str(e.pk))
        formset = response.context_data["inline_admin_formsets"][0].formset
        self.assertEqual(formset.total_form_count(), 1)
        self.assertEqual(formset.initial_form_count(), 1)