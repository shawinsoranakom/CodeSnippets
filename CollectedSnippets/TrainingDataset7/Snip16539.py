def test_explicit_autofield_inline(self):
        """
        A model with an explicit autofield primary key can be saved as inlines.
        """
        # First add a new inline
        self.post_data["grommet_set-0-name"] = "Grommet 1"
        collector_url = reverse(
            "admin:admin_views_collector_change", args=(self.collector.pk,)
        )
        response = self.client.post(collector_url, self.post_data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Grommet.objects.count(), 1)
        self.assertEqual(Grommet.objects.all()[0].name, "Grommet 1")

        # The PK link exists on the rendered form
        response = self.client.get(collector_url)
        self.assertContains(response, 'name="grommet_set-0-code"')

        # Now resave that inline
        self.post_data["grommet_set-INITIAL_FORMS"] = "1"
        self.post_data["grommet_set-0-code"] = str(Grommet.objects.all()[0].code)
        self.post_data["grommet_set-0-name"] = "Grommet 1"
        response = self.client.post(collector_url, self.post_data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Grommet.objects.count(), 1)
        self.assertEqual(Grommet.objects.all()[0].name, "Grommet 1")

        # Now modify that inline
        self.post_data["grommet_set-INITIAL_FORMS"] = "1"
        self.post_data["grommet_set-0-code"] = str(Grommet.objects.all()[0].code)
        self.post_data["grommet_set-0-name"] = "Grommet 1 Updated"
        response = self.client.post(collector_url, self.post_data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Grommet.objects.count(), 1)
        self.assertEqual(Grommet.objects.all()[0].name, "Grommet 1 Updated")