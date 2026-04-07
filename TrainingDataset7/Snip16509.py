def test_pluggable_search(self):
        PluggableSearchPerson.objects.create(name="Bob", age=10)
        PluggableSearchPerson.objects.create(name="Amy", age=20)

        response = self.client.get(
            reverse("admin:admin_views_pluggablesearchperson_changelist") + "?q=Bob"
        )
        # confirm the search returned one object
        self.assertContains(response, "\n1 pluggable search person\n")
        self.assertContains(response, "Bob")

        response = self.client.get(
            reverse("admin:admin_views_pluggablesearchperson_changelist") + "?q=20"
        )
        # confirm the search returned one object
        self.assertContains(response, "\n1 pluggable search person\n")
        self.assertContains(response, "Amy")