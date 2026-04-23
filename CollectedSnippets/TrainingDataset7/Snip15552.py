def test_inline_change_fk_change_perm(self):
        permission = Permission.objects.get(
            codename="change_inner2", content_type=self.inner_ct
        )
        self.user.user_permissions.add(permission)
        response = self.client.get(self.holder_change_url)
        # Change permission on inner2s, so we can change existing but not add
        # new
        self.assertContains(
            response,
            '<h2 id="inner2_set-heading" class="inline-heading">Inner2s</h2>',
            html=True,
        )
        self.assertContains(
            response,
            '<h2 id="inner2_set-2-heading" class="inline-heading">Inner2s</h2>',
            html=True,
        )
        # Just the one form for existing instances
        self.assertContains(
            response,
            '<input type="hidden" id="id_inner2_set-TOTAL_FORMS" value="1" '
            'name="inner2_set-TOTAL_FORMS">',
            html=True,
        )
        self.assertContains(
            response,
            '<input type="hidden" id="id_inner2_set-0-id" value="%s" '
            'name="inner2_set-0-id">' % self.inner2.id,
            html=True,
        )
        # max-num 0 means we can't add new ones
        self.assertContains(
            response,
            '<input type="hidden" id="id_inner2_set-MAX_NUM_FORMS" value="0" '
            'name="inner2_set-MAX_NUM_FORMS">',
            html=True,
        )
        # TabularInline
        self.assertContains(
            response, '<th class="column-dummy required">Dummy</th>', html=True
        )
        self.assertContains(
            response,
            '<input type="number" name="inner2_set-2-0-dummy" value="%s" '
            'class="vIntegerField" id="id_inner2_set-2-0-dummy">' % self.inner2.dummy,
            html=True,
        )