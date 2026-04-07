def test_item_link_error(self):
        """
        An ImproperlyConfigured is raised if no link could be found for the
        item(s).
        """
        msg = (
            "Give your Article class a get_absolute_url() method, or define "
            "an item_link() method in your Feed class."
        )
        with self.assertRaisesMessage(ImproperlyConfigured, msg):
            self.client.get("/syndication/articles/")