def test_max_num_param(self):
        """
        With extra=5 and max_num=2, there should be only 2 forms.
        """

        class MaxNumInline(GenericTabularInline):
            model = Media
            extra = 5
            max_num = 2

        modeladmin = admin.ModelAdmin(Episode, admin_site)
        modeladmin.inlines = [MaxNumInline]

        e = self._create_object(Episode)
        request = self.factory.get(
            reverse("admin:generic_inline_admin_episode_change", args=(e.pk,))
        )
        request.user = User(username="super", is_superuser=True)
        response = modeladmin.changeform_view(request, object_id=str(e.pk))
        formset = response.context_data["inline_admin_formsets"][0].formset
        self.assertEqual(formset.total_form_count(), 2)
        self.assertEqual(formset.initial_form_count(), 1)