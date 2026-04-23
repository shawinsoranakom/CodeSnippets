def test_inline_change_m2m_change_perm(self):
        permission = Permission.objects.get(
            codename="change_book", content_type=self.book_ct
        )
        self.user.user_permissions.add(permission)
        response = self.client.get(self.author_change_url)
        # We have change perm on books, so we can add/change/delete inlines
        self.assertIs(
            response.context["inline_admin_formset"].has_view_permission, True
        )
        self.assertIs(response.context["inline_admin_formset"].has_add_permission, True)
        self.assertIs(
            response.context["inline_admin_formset"].has_change_permission, True
        )
        self.assertIs(
            response.context["inline_admin_formset"].has_delete_permission, True
        )
        self.assertContains(
            response,
            (
                '<h2 id="Author_books-heading" class="inline-heading">'
                "Author-book relationships</h2>"
            ),
            html=True,
        )
        self.assertContains(response, "Add another Author-book relationship")
        self.assertContains(
            response,
            '<input type="hidden" id="id_Author_books-TOTAL_FORMS" '
            'value="4" name="Author_books-TOTAL_FORMS">',
            html=True,
        )
        self.assertContains(
            response,
            '<input type="hidden" id="id_Author_books-0-id" value="%s" '
            'name="Author_books-0-id">' % self.author_book_auto_m2m_intermediate_id,
            html=True,
        )
        self.assertContains(response, 'id="id_Author_books-0-DELETE"')