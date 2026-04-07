def test_inlines_plural_heading_foreign_key(self):
        response = self.client.get(reverse("admin:admin_inlines_holder4_add"))
        self.assertContains(
            response,
            (
                '<h2 id="inner4stacked_set-heading" class="inline-heading">'
                "Inner4 stackeds</h2>"
            ),
            html=True,
        )
        self.assertContains(
            response,
            (
                '<h2 id="inner4tabular_set-heading" class="inline-heading">'
                "Inner4 tabulars</h2>"
            ),
            html=True,
        )