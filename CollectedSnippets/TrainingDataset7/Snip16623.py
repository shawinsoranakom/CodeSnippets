def test_limit_choices_to(self):
        """Regression test for 14880"""
        actor = Actor.objects.create(name="Palin", age=27)
        Inquisition.objects.create(expected=True, leader=actor, country="England")
        Inquisition.objects.create(expected=False, leader=actor, country="Spain")
        response = self.client.get(reverse("admin:admin_views_sketch_add"))
        # Find the link
        m = re.search(
            rb'<a href="([^"]*)"[^>]* id="lookup_id_inquisition"', response.content
        )
        self.assertTrue(m)  # Got a match
        popup_url = m[1].decode().replace("&amp;", "&")

        # Handle relative links
        popup_url = urljoin(response.request["PATH_INFO"], popup_url)
        # Get the popup and verify the correct objects show up in the resulting
        # page. This step also tests integers, strings and booleans in the
        # lookup query string; in model we define inquisition field to have a
        # limit_choices_to option that includes a filter on a string field
        # (inquisition__actor__name), a filter on an integer field
        # (inquisition__actor__age), and a filter on a boolean field
        # (inquisition__expected).
        response2 = self.client.get(popup_url)
        self.assertContains(response2, "Spain")
        self.assertNotContains(response2, "England")