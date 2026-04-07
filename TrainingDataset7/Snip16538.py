def test_simple_inline(self):
        "A simple model can be saved as inlines"
        # First add a new inline
        self.post_data["widget_set-0-name"] = "Widget 1"
        collector_url = reverse(
            "admin:admin_views_collector_change", args=(self.collector.pk,)
        )
        response = self.client.post(collector_url, self.post_data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Widget.objects.count(), 1)
        self.assertEqual(Widget.objects.all()[0].name, "Widget 1")
        widget_id = Widget.objects.all()[0].id

        # The PK link exists on the rendered form
        response = self.client.get(collector_url)
        self.assertContains(response, 'name="widget_set-0-id"')

        # No file or image fields, no enctype on the forms
        self.assertIs(response.context["has_file_field"], False)
        self.assertNotContains(response, MULTIPART_ENCTYPE)

        # Now resave that inline
        self.post_data["widget_set-INITIAL_FORMS"] = "1"
        self.post_data["widget_set-0-id"] = str(widget_id)
        self.post_data["widget_set-0-name"] = "Widget 1"
        response = self.client.post(collector_url, self.post_data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Widget.objects.count(), 1)
        self.assertEqual(Widget.objects.all()[0].name, "Widget 1")

        # Now modify that inline
        self.post_data["widget_set-INITIAL_FORMS"] = "1"
        self.post_data["widget_set-0-id"] = str(widget_id)
        self.post_data["widget_set-0-name"] = "Widget 1 Updated"
        response = self.client.post(collector_url, self.post_data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Widget.objects.count(), 1)
        self.assertEqual(Widget.objects.all()[0].name, "Widget 1 Updated")