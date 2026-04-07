def test_min_num(self):
        """
        min_num and extra determine number of forms.
        """

        class MinNumInline(TabularInline):
            model = BinaryTree
            min_num = 2
            extra = 3

        modeladmin = ModelAdmin(BinaryTree, admin_site)
        modeladmin.inlines = [MinNumInline]
        min_forms = (
            '<input id="id_binarytree_set-MIN_NUM_FORMS" '
            'name="binarytree_set-MIN_NUM_FORMS" type="hidden" value="2">'
        )
        total_forms = (
            '<input id="id_binarytree_set-TOTAL_FORMS" '
            'name="binarytree_set-TOTAL_FORMS" type="hidden" value="5">'
        )
        request = self.factory.get(reverse("admin:admin_inlines_binarytree_add"))
        request.user = User(username="super", is_superuser=True)
        response = modeladmin.changeform_view(request)
        self.assertInHTML(min_forms, response.rendered_content)
        self.assertInHTML(total_forms, response.rendered_content)