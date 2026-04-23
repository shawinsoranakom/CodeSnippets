def test_can_delete(self):
        """
        can_delete should be passed to inlineformset factory.
        """
        response = self.client.get(
            reverse("admin:admin_inlines_holder_change", args=(self.holder.id,))
        )
        inner_formset = response.context["inline_admin_formsets"][0].formset
        expected = InnerInline.can_delete
        actual = inner_formset.can_delete
        self.assertEqual(expected, actual, "can_delete must be equal")