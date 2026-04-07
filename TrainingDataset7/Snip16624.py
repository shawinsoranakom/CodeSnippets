def test_limit_choices_to_isnull_false(self):
        """Regression test for 20182"""
        Actor.objects.create(name="Palin", age=27)
        Actor.objects.create(name="Kilbraken", age=50, title="Judge")
        response = self.client.get(reverse("admin:admin_views_sketch_add"))
        # Find the link
        m = re.search(
            rb'<a href="([^"]*)"[^>]* id="lookup_id_defendant0"', response.content
        )
        self.assertTrue(m)  # Got a match
        popup_url = m[1].decode().replace("&amp;", "&")

        # Handle relative links
        popup_url = urljoin(response.request["PATH_INFO"], popup_url)
        # Get the popup and verify the correct objects show up in the resulting
        # page. This step tests field__isnull=0 gets parsed correctly from the
        # lookup query string; in model we define defendant0 field to have a
        # limit_choices_to option that includes "actor__title__isnull=False".
        response2 = self.client.get(popup_url)
        self.assertContains(response2, "Kilbraken")
        self.assertNotContains(response2, "Palin")