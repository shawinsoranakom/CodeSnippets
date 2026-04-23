def test_inline_change_fk_add_perm(self):
        permission = Permission.objects.get(
            codename="add_inner2", content_type=self.inner_ct
        )
        self.user.user_permissions.add(permission)
        response = self.client.get(self.holder_change_url)
        # Add permission on inner2s, so we can add but not modify existing
        self.assertContains(
            response,
            '<h2 id="inner2_set-2-heading" class="inline-heading">Inner2s</h2>',
            html=True,
        )
        self.assertContains(response, "Add another Inner2")
        # 3 extra forms only, not the existing instance form
        self.assertContains(
            response,
            '<input type="hidden" id="id_inner2_set-TOTAL_FORMS" value="3" '
            'name="inner2_set-TOTAL_FORMS">',
            html=True,
        )
        self.assertNotContains(
            response,
            '<input type="hidden" id="id_inner2_set-0-id" value="%s" '
            'name="inner2_set-0-id">' % self.inner2.id,
            html=True,
        )