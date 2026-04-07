def test_inline_change_fk_noperm(self):
        response = self.client.get(self.holder_change_url)
        # No permissions on Inner2s, so no inline
        self.assertNotContains(
            response,
            '<h2 id="inner2_set-2-heading" class="inline-heading">Inner2s</h2>',
            html=True,
        )
        self.assertNotContains(response, "Add another Inner2")
        self.assertNotContains(response, 'id="id_inner2_set-TOTAL_FORMS"')