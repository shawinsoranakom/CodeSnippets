def test_recentactions_link(self):
        """
        The link from the recent actions list referring to the changeform of
        the object should be quoted.
        """
        response = self.client.get(reverse("admin:index"))
        link = reverse(
            "admin:admin_views_modelwithstringprimarykey_change", args=(quote(self.pk),)
        )
        should_contain = """<a href="%s">%s</a>""" % (escape(link), escape(self.pk))
        self.assertContains(response, should_contain)