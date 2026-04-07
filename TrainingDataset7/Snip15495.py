def test_excluded_id_for_inlines_uses_hidden_field(self):
        parent = UUIDParent.objects.create()
        child = UUIDChild.objects.create(title="foo", parent=parent)
        response = self.client.get(
            reverse("admin:admin_inlines_uuidparent_change", args=(parent.id,))
        )
        self.assertContains(
            response,
            f'<input type="hidden" name="uuidchild_set-0-id" value="{child.id}" '
            'id="id_uuidchild_set-0-id">',
            html=True,
        )