def test_bookmarklets(self):
        response = self.client.get(reverse("django-admindocs-bookmarklets"))
        self.assertContains(response, "/admindocs/views/")