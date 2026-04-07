def test_custom_get_extra_form(self):
        bt_head = BinaryTree.objects.create(name="Tree Head")
        BinaryTree.objects.create(name="First Child", parent=bt_head)
        # The maximum number of forms should respect 'get_max_num' on the
        # ModelAdmin
        max_forms_input = (
            '<input id="id_binarytree_set-MAX_NUM_FORMS" '
            'name="binarytree_set-MAX_NUM_FORMS" type="hidden" value="%d">'
        )
        # The total number of forms will remain the same in either case
        total_forms_hidden = (
            '<input id="id_binarytree_set-TOTAL_FORMS" '
            'name="binarytree_set-TOTAL_FORMS" type="hidden" value="2">'
        )
        response = self.client.get(reverse("admin:admin_inlines_binarytree_add"))
        self.assertInHTML(max_forms_input % 3, response.rendered_content)
        self.assertInHTML(total_forms_hidden, response.rendered_content)

        response = self.client.get(
            reverse("admin:admin_inlines_binarytree_change", args=(bt_head.id,))
        )
        self.assertInHTML(max_forms_input % 2, response.rendered_content)
        self.assertInHTML(total_forms_hidden, response.rendered_content)