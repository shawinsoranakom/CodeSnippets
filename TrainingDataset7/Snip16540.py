def test_char_pk_inline(self):
        """
        A model with a character PK can be saved as inlines. Regression for
        #10992
        """
        # First add a new inline
        self.post_data["doohickey_set-0-code"] = "DH1"
        self.post_data["doohickey_set-0-name"] = "Doohickey 1"
        collector_url = reverse(
            "admin:admin_views_collector_change", args=(self.collector.pk,)
        )
        response = self.client.post(collector_url, self.post_data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(DooHickey.objects.count(), 1)
        self.assertEqual(DooHickey.objects.all()[0].name, "Doohickey 1")

        # The PK link exists on the rendered form
        response = self.client.get(collector_url)
        self.assertContains(response, 'name="doohickey_set-0-code"')

        # Now resave that inline
        self.post_data["doohickey_set-INITIAL_FORMS"] = "1"
        self.post_data["doohickey_set-0-code"] = "DH1"
        self.post_data["doohickey_set-0-name"] = "Doohickey 1"
        response = self.client.post(collector_url, self.post_data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(DooHickey.objects.count(), 1)
        self.assertEqual(DooHickey.objects.all()[0].name, "Doohickey 1")

        # Now modify that inline
        self.post_data["doohickey_set-INITIAL_FORMS"] = "1"
        self.post_data["doohickey_set-0-code"] = "DH1"
        self.post_data["doohickey_set-0-name"] = "Doohickey 1 Updated"
        response = self.client.post(collector_url, self.post_data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(DooHickey.objects.count(), 1)
        self.assertEqual(DooHickey.objects.all()[0].name, "Doohickey 1 Updated")