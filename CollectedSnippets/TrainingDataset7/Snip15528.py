def test_noneditable_inline_has_field_inputs(self):
        """Inlines without change permission shows field inputs on add form."""
        response = self.client.get(
            reverse("admin:admin_inlines_novelreadonlychapter_add")
        )
        self.assertContains(
            response,
            '<input type="text" name="chapter_set-0-name" '
            'class="vTextField" maxlength="40" id="id_chapter_set-0-name">',
            html=True,
        )