def test_limit_choices_to_as_callable(self):
        """Test for ticket 2445 changes to admin."""
        threepwood = Character.objects.create(
            username="threepwood",
            last_action=datetime.datetime.today() + datetime.timedelta(days=1),
        )
        marley = Character.objects.create(
            username="marley",
            last_action=datetime.datetime.today() - datetime.timedelta(days=1),
        )
        response = self.client.get(reverse("admin:admin_views_stumpjoke_add"))
        # The allowed option should appear twice; the limited option should not
        # appear.
        self.assertContains(response, threepwood.username, count=2)
        self.assertNotContains(response, marley.username)