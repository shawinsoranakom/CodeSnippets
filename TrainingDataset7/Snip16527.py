def test_add_model_modeladmin_defer_qs(self):
        # Test for #14529. defer() is used in ModelAdmin.get_queryset()

        # model has __str__ method
        self.assertEqual(CoverLetter.objects.count(), 0)
        # Emulate model instance creation via the admin
        post_data = {
            "author": "Candidate, Best",
            "_save": "Save",
        }
        response = self.client.post(
            reverse("admin:admin_views_coverletter_add"), post_data, follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(CoverLetter.objects.count(), 1)
        # Message should contain non-ugly model verbose name
        pk = CoverLetter.objects.all()[0].pk
        self.assertContains(
            response,
            '<li class="success">The cover letter “<a href="%s">'
            "Candidate, Best</a>” was added successfully.</li>"
            % reverse("admin:admin_views_coverletter_change", args=(pk,)),
            html=True,
        )

        # model has no __str__ method
        self.assertEqual(ShortMessage.objects.count(), 0)
        # Emulate model instance creation via the admin
        post_data = {
            "content": "What's this SMS thing?",
            "_save": "Save",
        }
        response = self.client.post(
            reverse("admin:admin_views_shortmessage_add"), post_data, follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(ShortMessage.objects.count(), 1)
        # Message should contain non-ugly model verbose name
        sm = ShortMessage.objects.all()[0]
        self.assertContains(
            response,
            '<li class="success">The short message “<a href="%s">'
            "%s</a>” was added successfully.</li>"
            % (reverse("admin:admin_views_shortmessage_change", args=(sm.pk,)), sm),
            html=True,
        )