def test_inline_add_m2m_view_only_perm(self):
        permission = Permission.objects.get(
            codename="view_book", content_type=self.book_ct
        )
        self.user.user_permissions.add(permission)
        response = self.client.get(reverse("admin:admin_inlines_author_add"))
        # View-only inlines. (It could be nicer to hide the empty, non-editable
        # inlines on the add page.)
        self.assertIs(
            response.context["inline_admin_formset"].has_view_permission, True
        )
        self.assertIs(
            response.context["inline_admin_formset"].has_add_permission, False
        )
        self.assertIs(
            response.context["inline_admin_formset"].has_change_permission, False
        )
        self.assertIs(
            response.context["inline_admin_formset"].has_delete_permission, False
        )
        self.assertContains(
            response,
            (
                '<h2 id="Author_books-heading" class="inline-heading">'
                "Author-book relationships</h2>"
            ),
            html=True,
        )
        self.assertContains(
            response,
            '<input type="hidden" name="Author_books-TOTAL_FORMS" value="0" '
            'id="id_Author_books-TOTAL_FORMS">',
            html=True,
        )
        self.assertNotContains(response, "Add another Author-Book Relationship")