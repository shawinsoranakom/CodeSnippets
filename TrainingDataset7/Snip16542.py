def test_inherited_inline(self):
        "An inherited model can be saved as inlines. Regression for #11042"
        # First add a new inline
        self.post_data["fancydoodad_set-0-name"] = "Fancy Doodad 1"
        collector_url = reverse(
            "admin:admin_views_collector_change", args=(self.collector.pk,)
        )
        response = self.client.post(collector_url, self.post_data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(FancyDoodad.objects.count(), 1)
        self.assertEqual(FancyDoodad.objects.all()[0].name, "Fancy Doodad 1")
        doodad_pk = FancyDoodad.objects.all()[0].pk

        # The PK link exists on the rendered form
        response = self.client.get(collector_url)
        self.assertContains(response, 'name="fancydoodad_set-0-doodad_ptr"')

        # Now resave that inline
        self.post_data["fancydoodad_set-INITIAL_FORMS"] = "1"
        self.post_data["fancydoodad_set-0-doodad_ptr"] = str(doodad_pk)
        self.post_data["fancydoodad_set-0-name"] = "Fancy Doodad 1"
        response = self.client.post(collector_url, self.post_data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(FancyDoodad.objects.count(), 1)
        self.assertEqual(FancyDoodad.objects.all()[0].name, "Fancy Doodad 1")

        # Now modify that inline
        self.post_data["fancydoodad_set-INITIAL_FORMS"] = "1"
        self.post_data["fancydoodad_set-0-doodad_ptr"] = str(doodad_pk)
        self.post_data["fancydoodad_set-0-name"] = "Fancy Doodad 1 Updated"
        response = self.client.post(collector_url, self.post_data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(FancyDoodad.objects.count(), 1)
        self.assertEqual(FancyDoodad.objects.all()[0].name, "Fancy Doodad 1 Updated")