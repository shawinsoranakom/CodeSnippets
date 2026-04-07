def test_no_param(self):
        """
        With one initial form, extra (default) at 3, there should be 4 forms.
        """
        e = self._create_object(Episode)
        response = self.client.get(
            reverse("admin:generic_inline_admin_episode_change", args=(e.pk,))
        )
        formset = response.context["inline_admin_formsets"][0].formset
        self.assertEqual(formset.total_form_count(), 4)
        self.assertEqual(formset.initial_form_count(), 1)