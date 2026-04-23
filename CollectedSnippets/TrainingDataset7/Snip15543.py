def test_inline_change_m2m_noperm(self):
        response = self.client.get(self.author_change_url)
        # No change permission on books, so no inline
        self.assertNotContains(
            response,
            (
                '<h2 id="Author_books-heading" class="inline-heading">'
                "Author-book relationships</h2>"
            ),
            html=True,
        )
        self.assertNotContains(response, "Add another Author-Book Relationship")
        self.assertNotContains(response, 'id="id_Author_books-TOTAL_FORMS"')