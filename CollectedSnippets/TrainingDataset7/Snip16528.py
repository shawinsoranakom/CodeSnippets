def test_add_model_modeladmin_only_qs(self):
        # Test for #14529. only() is used in ModelAdmin.get_queryset()

        # model has __str__ method
        self.assertEqual(Telegram.objects.count(), 0)
        # Emulate model instance creation via the admin
        post_data = {
            "title": "Urgent telegram",
            "_save": "Save",
        }
        response = self.client.post(
            reverse("admin:admin_views_telegram_add"), post_data, follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Telegram.objects.count(), 1)
        # Message should contain non-ugly model verbose name
        pk = Telegram.objects.all()[0].pk
        self.assertContains(
            response,
            '<li class="success">The telegram “<a href="%s">'
            "Urgent telegram</a>” was added successfully.</li>"
            % reverse("admin:admin_views_telegram_change", args=(pk,)),
            html=True,
        )

        # model has no __str__ method
        self.assertEqual(Paper.objects.count(), 0)
        # Emulate model instance creation via the admin
        post_data = {
            "title": "My Modified Paper Title",
            "_save": "Save",
        }
        response = self.client.post(
            reverse("admin:admin_views_paper_add"), post_data, follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Paper.objects.count(), 1)
        # Message should contain non-ugly model verbose name
        p = Paper.objects.all()[0]
        self.assertContains(
            response,
            '<li class="success">The paper “<a href="%s">'
            "%s</a>” was added successfully.</li>"
            % (reverse("admin:admin_views_paper_change", args=(p.pk,)), p),
            html=True,
        )