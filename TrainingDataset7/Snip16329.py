def test_popup_dismiss_related(self):
        """
        Regression test for ticket 20664 - ensure the pk is properly quoted.
        """
        actor = Actor.objects.create(name="Palin", age=27)
        response = self.client.get(
            "%s?%s" % (reverse("admin:admin_views_actor_changelist"), IS_POPUP_VAR)
        )
        self.assertContains(response, 'data-popup-opener="%s"' % actor.pk)