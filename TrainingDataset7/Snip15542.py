def test_inline_add_fk_noperm(self):
        response = self.client.get(reverse("admin:admin_inlines_holder2_add"))
        # No permissions on Inner2s, so no inline
        self.assertNotContains(
            response,
            '<h2 id="inner2_set-2-heading" class="inline-heading">Inner2s</h2>',
            html=True,
        )
        self.assertNotContains(response, "Add another Inner2")
        self.assertNotContains(response, 'id="id_inner2_set-TOTAL_FORMS"')