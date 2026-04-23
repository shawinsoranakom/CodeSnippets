def test_no_standard_modeladmin_urls(self):
        """
        Admin index views don't break when user's ModelAdmin removes standard
        urls
        """
        self.client.force_login(self.changeuser)
        r = self.client.get(reverse("admin:index"))
        # we shouldn't get a 500 error caused by a NoReverseMatch
        self.assertEqual(r.status_code, 200)
        self.client.post(reverse("admin:logout"))