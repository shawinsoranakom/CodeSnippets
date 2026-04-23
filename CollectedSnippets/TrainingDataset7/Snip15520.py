def test_custom_min_num(self):
        bt_head = BinaryTree.objects.create(name="Tree Head")
        BinaryTree.objects.create(name="First Child", parent=bt_head)

        class MinNumInline(TabularInline):
            model = BinaryTree
            extra = 3

            def get_min_num(self, request, obj=None, **kwargs):
                if obj:
                    return 5
                return 2

        modeladmin = ModelAdmin(BinaryTree, admin_site)
        modeladmin.inlines = [MinNumInline]
        min_forms = (
            '<input id="id_binarytree_set-MIN_NUM_FORMS" '
            'name="binarytree_set-MIN_NUM_FORMS" type="hidden" value="%d">'
        )
        total_forms = (
            '<input id="id_binarytree_set-TOTAL_FORMS" '
            'name="binarytree_set-TOTAL_FORMS" type="hidden" value="%d">'
        )
        request = self.factory.get(reverse("admin:admin_inlines_binarytree_add"))
        request.user = User(username="super", is_superuser=True)
        response = modeladmin.changeform_view(request)
        self.assertInHTML(min_forms % 2, response.rendered_content)
        self.assertInHTML(total_forms % 5, response.rendered_content)

        request = self.factory.get(
            reverse("admin:admin_inlines_binarytree_change", args=(bt_head.id,))
        )
        request.user = User(username="super", is_superuser=True)
        response = modeladmin.changeform_view(request, object_id=str(bt_head.id))
        self.assertInHTML(min_forms % 5, response.rendered_content)
        self.assertInHTML(total_forms % 8, response.rendered_content)