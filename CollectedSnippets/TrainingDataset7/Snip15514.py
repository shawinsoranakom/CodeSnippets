def test_non_related_name_inline(self):
        """
        Multiple inlines with related_name='+' have correct form prefixes.
        """
        response = self.client.get(reverse("admin:admin_inlines_capofamiglia_add"))
        self.assertContains(
            response, '<input type="hidden" name="-1-0-id" id="id_-1-0-id">', html=True
        )
        self.assertContains(
            response,
            '<input type="hidden" name="-1-0-capo_famiglia" '
            'id="id_-1-0-capo_famiglia">',
            html=True,
        )
        self.assertContains(
            response,
            '<input id="id_-1-0-name" type="text" class="vTextField" name="-1-0-name" '
            'maxlength="100" aria-describedby="id_-1-0-name_helptext">',
            html=True,
        )
        self.assertContains(
            response, '<input type="hidden" name="-2-0-id" id="id_-2-0-id">', html=True
        )
        self.assertContains(
            response,
            '<input type="hidden" name="-2-0-capo_famiglia" '
            'id="id_-2-0-capo_famiglia">',
            html=True,
        )
        self.assertContains(
            response,
            '<input id="id_-2-0-name" type="text" class="vTextField" name="-2-0-name" '
            'maxlength="100">',
            html=True,
        )