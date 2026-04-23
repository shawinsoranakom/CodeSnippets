def test_callable(self):
        "The right link is displayed if view_on_site is a callable"
        response = self.client.get(
            reverse("admin:admin_views_restaurant_change", args=(self.r1.pk,))
        )
        self.assertContains(
            response, '"/worker_inline/%s/%s/"' % (self.w1.surname, self.w1.name)
        )