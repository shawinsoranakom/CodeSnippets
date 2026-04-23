def test_stacked_inline_edit_form_contains_has_original_class(self):
        holder = Holder.objects.create(dummy=1)
        holder.inner_set.create(dummy=1)
        response = self.client.get(
            reverse("admin:admin_inlines_holder_change", args=(holder.pk,))
        )
        self.assertContains(
            response,
            '<div class="inline-related has_original" id="inner_set-0">',
            count=1,
        )
        self.assertContains(
            response, '<div class="inline-related" id="inner_set-1">', count=1
        )