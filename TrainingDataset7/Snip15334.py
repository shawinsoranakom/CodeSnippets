def test_templatefilter_index(self):
        response = self.client.get(reverse("django-admindocs-filters"))
        self.assertContains(response, '<h3 id="built_in-first">first</h3>', html=True)