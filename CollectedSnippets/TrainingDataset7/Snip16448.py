def test_cyclic(self):
        """
        Cyclic relationships should still cause each object to only be
        listed once.
        """
        one = '<li>Cyclic one: <a href="%s">I am recursive</a>' % (
            reverse("admin:admin_views_cyclicone_change", args=(self.cy1.pk,)),
        )
        two = '<li>Cyclic two: <a href="%s">I am recursive too</a>' % (
            reverse("admin:admin_views_cyclictwo_change", args=(self.cy2.pk,)),
        )
        response = self.client.get(
            reverse("admin:admin_views_cyclicone_delete", args=(self.cy1.pk,))
        )

        self.assertContains(response, one, 1)
        self.assertContains(response, two, 1)