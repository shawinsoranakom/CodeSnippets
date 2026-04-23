def test_beginning_matches(self):
        response = self.client.get(
            reverse("admin:admin_views_person_changelist") + "?q=Gui"
        )
        # confirm the search returned one object
        self.assertContains(response, "\n1 person\n")
        self.assertContains(response, "Guido")

        response = self.client.get(
            reverse("admin:admin_views_person_changelist") + "?q=uido"
        )
        # confirm the search returned zero objects
        self.assertContains(response, "\n0 persons\n")
        self.assertNotContains(response, "Guido")