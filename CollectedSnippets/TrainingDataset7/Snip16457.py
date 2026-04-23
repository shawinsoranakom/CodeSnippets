def test_inheritance(self):
        """
        In the case of an inherited model, if either the child or
        parent-model instance is deleted, both instances are listed
        for deletion, as well as any relationships they have.
        """
        should_contain = [
            '<li>Villain: <a href="%s">Bob</a>'
            % reverse("admin:admin_views_villain_change", args=(self.sv1.pk,)),
            '<li>Super villain: <a href="%s">Bob</a>'
            % reverse("admin:admin_views_supervillain_change", args=(self.sv1.pk,)),
            "<li>Secret hideout: floating castle",
            "<li>Super secret hideout: super floating castle!",
        ]
        response = self.client.get(
            reverse("admin:admin_views_villain_delete", args=(self.sv1.pk,))
        )
        for should in should_contain:
            self.assertContains(response, should, 1)
        response = self.client.get(
            reverse("admin:admin_views_supervillain_delete", args=(self.sv1.pk,))
        )
        for should in should_contain:
            self.assertContains(response, should, 1)