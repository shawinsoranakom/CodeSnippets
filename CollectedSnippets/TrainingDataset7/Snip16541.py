def test_integer_pk_inline(self):
        """
        A model with an integer PK can be saved as inlines. Regression for
        #10992
        """
        # First add a new inline
        self.post_data["whatsit_set-0-index"] = "42"
        self.post_data["whatsit_set-0-name"] = "Whatsit 1"
        collector_url = reverse(
            "admin:admin_views_collector_change", args=(self.collector.pk,)
        )
        response = self.client.post(collector_url, self.post_data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Whatsit.objects.count(), 1)
        self.assertEqual(Whatsit.objects.all()[0].name, "Whatsit 1")

        # The PK link exists on the rendered form
        response = self.client.get(collector_url)
        self.assertContains(response, 'name="whatsit_set-0-index"')

        # Now resave that inline
        self.post_data["whatsit_set-INITIAL_FORMS"] = "1"
        self.post_data["whatsit_set-0-index"] = "42"
        self.post_data["whatsit_set-0-name"] = "Whatsit 1"
        response = self.client.post(collector_url, self.post_data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Whatsit.objects.count(), 1)
        self.assertEqual(Whatsit.objects.all()[0].name, "Whatsit 1")

        # Now modify that inline
        self.post_data["whatsit_set-INITIAL_FORMS"] = "1"
        self.post_data["whatsit_set-0-index"] = "42"
        self.post_data["whatsit_set-0-name"] = "Whatsit 1 Updated"
        response = self.client.post(collector_url, self.post_data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Whatsit.objects.count(), 1)
        self.assertEqual(Whatsit.objects.all()[0].name, "Whatsit 1 Updated")