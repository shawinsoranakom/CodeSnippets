def test_inline_add_fk_add_perm(self):
        permission = Permission.objects.get(
            codename="add_inner2", content_type=self.inner_ct
        )
        self.user.user_permissions.add(permission)
        response = self.client.get(reverse("admin:admin_inlines_holder2_add"))
        # Add permission on inner2s, so we get the inline
        self.assertContains(
            response,
            '<h2 id="inner2_set-2-heading" class="inline-heading">Inner2s</h2>',
            html=True,
        )
        self.assertContains(response, "Add another Inner2")
        self.assertContains(
            response,
            '<input type="hidden" id="id_inner2_set-TOTAL_FORMS" '
            'value="3" name="inner2_set-TOTAL_FORMS">',
            html=True,
        )