def test_inline_change_m2m_view_only_perm(self):
        permission = Permission.objects.get(
            codename="view_book", content_type=self.book_ct
        )
        self.user.user_permissions.add(permission)
        response = self.client.get(self.author_change_url)
        # View-only inlines.
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
            '<input type="hidden" name="Author_books-TOTAL_FORMS" value="1" '
            'id="id_Author_books-TOTAL_FORMS">',
            html=True,
        )
        # The field in the inline is read-only.
        self.assertContains(response, "<p>%s</p>" % self.book)
        self.assertNotContains(
            response,
            '<input type="checkbox" name="Author_books-0-DELETE" '
            'id="id_Author_books-0-DELETE">',
            html=True,
        )