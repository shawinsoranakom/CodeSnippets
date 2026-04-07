def test_templatetag_index(self):
        response = self.client.get(reverse("django-admindocs-tags"))
        self.assertContains(
            response, '<h3 id="built_in-extends">extends</h3>', html=True
        )