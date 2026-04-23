def test_inline_change_fk_add_change_perm(self):
        permission = Permission.objects.get(
            codename="add_inner2", content_type=self.inner_ct
        )
        self.user.user_permissions.add(permission)
        permission = Permission.objects.get(
            codename="change_inner2", content_type=self.inner_ct
        )
        self.user.user_permissions.add(permission)
        response = self.client.get(self.holder_change_url)
        # Add/change perm, so we can add new and change existing
        self.assertContains(
            response,
            '<h2 id="inner2_set-2-heading" class="inline-heading">Inner2s</h2>',
            html=True,
        )
        # One form for existing instance and three extra for new
        self.assertContains(
            response,
            '<input type="hidden" id="id_inner2_set-TOTAL_FORMS" value="4" '
            'name="inner2_set-TOTAL_FORMS">',
            html=True,
        )
        self.assertContains(
            response,
            '<input type="hidden" id="id_inner2_set-0-id" value="%s" '
            'name="inner2_set-0-id">' % self.inner2.id,
            html=True,
        )