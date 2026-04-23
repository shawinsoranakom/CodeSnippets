def test_unicode_edit(self):
        """
        A test to ensure that POST on edit_view handles non-ASCII characters.
        """
        post_data = {
            "name": "Test lærdommer",
            # inline data
            "chapter_set-TOTAL_FORMS": "6",
            "chapter_set-INITIAL_FORMS": "3",
            "chapter_set-MAX_NUM_FORMS": "0",
            "chapter_set-0-id": self.chap1.pk,
            "chapter_set-0-title": "Norske bostaver æøå skaper problemer",
            "chapter_set-0-content": (
                "&lt;p&gt;Svært frustrerende med UnicodeDecodeError&lt;/p&gt;"
            ),
            "chapter_set-1-id": self.chap2.id,
            "chapter_set-1-title": "Kjærlighet.",
            "chapter_set-1-content": (
                "&lt;p&gt;La kjærligheten til de lidende seire.&lt;/p&gt;"
            ),
            "chapter_set-2-id": self.chap3.id,
            "chapter_set-2-title": "Need a title.",
            "chapter_set-2-content": "&lt;p&gt;Newest content&lt;/p&gt;",
            "chapter_set-3-id": "",
            "chapter_set-3-title": "",
            "chapter_set-3-content": "",
            "chapter_set-4-id": "",
            "chapter_set-4-title": "",
            "chapter_set-4-content": "",
            "chapter_set-5-id": "",
            "chapter_set-5-title": "",
            "chapter_set-5-content": "",
        }

        response = self.client.post(
            reverse("admin:admin_views_book_change", args=(self.b1.pk,)), post_data
        )
        self.assertEqual(response.status_code, 302)