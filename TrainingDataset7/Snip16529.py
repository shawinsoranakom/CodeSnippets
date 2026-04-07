def test_edit_model_modeladmin_defer_qs(self):
        # Test for #14529. defer() is used in ModelAdmin.get_queryset()

        # model has __str__ method
        cl = CoverLetter.objects.create(author="John Doe")
        self.assertEqual(CoverLetter.objects.count(), 1)
        response = self.client.get(
            reverse("admin:admin_views_coverletter_change", args=(cl.pk,))
        )
        self.assertEqual(response.status_code, 200)
        # Emulate model instance edit via the admin
        post_data = {
            "author": "John Doe II",
            "_save": "Save",
        }
        url = reverse("admin:admin_views_coverletter_change", args=(cl.pk,))
        response = self.client.post(url, post_data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(CoverLetter.objects.count(), 1)
        # Message should contain non-ugly model verbose name. Instance
        # representation is set by model's __str__()
        self.assertContains(
            response,
            '<li class="success">The cover letter “<a href="%s">'
            "John Doe II</a>” was changed successfully.</li>"
            % reverse("admin:admin_views_coverletter_change", args=(cl.pk,)),
            html=True,
        )

        # model has no __str__ method
        sm = ShortMessage.objects.create(content="This is expensive")
        self.assertEqual(ShortMessage.objects.count(), 1)
        response = self.client.get(
            reverse("admin:admin_views_shortmessage_change", args=(sm.pk,))
        )
        self.assertEqual(response.status_code, 200)
        # Emulate model instance edit via the admin
        post_data = {
            "content": "Too expensive",
            "_save": "Save",
        }
        url = reverse("admin:admin_views_shortmessage_change", args=(sm.pk,))
        response = self.client.post(url, post_data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(ShortMessage.objects.count(), 1)
        # Message should contain non-ugly model verbose name. The ugly(!)
        # instance representation is set by __str__().
        self.assertContains(
            response,
            '<li class="success">The short message “<a href="%s">'
            "%s</a>” was changed successfully.</li>"
            % (reverse("admin:admin_views_shortmessage_change", args=(sm.pk,)), sm),
            html=True,
        )