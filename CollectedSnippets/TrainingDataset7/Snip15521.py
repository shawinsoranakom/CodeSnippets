def test_inline_nonauto_noneditable_pk(self):
        response = self.client.get(reverse("admin:admin_inlines_author_add"))
        self.assertContains(
            response,
            '<input id="id_nonautopkbook_set-0-rand_pk" '
            'name="nonautopkbook_set-0-rand_pk" type="hidden">',
            html=True,
        )
        self.assertContains(
            response,
            '<input id="id_nonautopkbook_set-2-0-rand_pk" '
            'name="nonautopkbook_set-2-0-rand_pk" type="hidden">',
            html=True,
        )