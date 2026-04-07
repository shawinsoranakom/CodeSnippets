def test_inline_editable_pk(self):
        response = self.client.get(reverse("admin:admin_inlines_author_add"))
        self.assertContains(
            response,
            '<input class="vIntegerField" id="id_editablepkbook_set-0-manual_pk" '
            'name="editablepkbook_set-0-manual_pk" type="number">',
            html=True,
            count=1,
        )
        self.assertContains(
            response,
            '<input class="vIntegerField" id="id_editablepkbook_set-2-0-manual_pk" '
            'name="editablepkbook_set-2-0-manual_pk" type="number">',
            html=True,
            count=1,
        )