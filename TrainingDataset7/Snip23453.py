def test_min_num_param(self):
        """
        With extra=3 and min_num=2, there should be five forms.
        """

        class MinNumInline(GenericTabularInline):
            model = Media
            extra = 3
            min_num = 2

        modeladmin = admin.ModelAdmin(Episode, admin_site)
        modeladmin.inlines = [MinNumInline]

        e = self._create_object(Episode)
        request = self.factory.get(
            reverse("admin:generic_inline_admin_episode_change", args=(e.pk,))
        )
        request.user = User(username="super", is_superuser=True)
        response = modeladmin.changeform_view(request, object_id=str(e.pk))
        formset = response.context_data["inline_admin_formsets"][0].formset
        self.assertEqual(formset.total_form_count(), 5)
        self.assertEqual(formset.initial_form_count(), 1)