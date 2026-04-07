def test_inlines_singular_heading_one_to_one(self):
        response = self.client.get(reverse("admin:admin_inlines_person_add"))
        self.assertContains(
            response,
            '<h2 id="author-heading" class="inline-heading">Author</h2>',
            html=True,
        )  # Tabular.
        self.assertContains(
            response,
            '<h2 id="fashionista-heading" class="inline-heading">Fashionista</h2>',
            html=True,
        )