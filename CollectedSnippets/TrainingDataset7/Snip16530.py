def test_edit_model_modeladmin_only_qs(self):
        # Test for #14529. only() is used in ModelAdmin.get_queryset()

        # model has __str__ method
        t = Telegram.objects.create(title="First Telegram")
        self.assertEqual(Telegram.objects.count(), 1)
        response = self.client.get(
            reverse("admin:admin_views_telegram_change", args=(t.pk,))
        )
        self.assertEqual(response.status_code, 200)
        # Emulate model instance edit via the admin
        post_data = {
            "title": "Telegram without typo",
            "_save": "Save",
        }
        response = self.client.post(
            reverse("admin:admin_views_telegram_change", args=(t.pk,)),
            post_data,
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Telegram.objects.count(), 1)
        # Message should contain non-ugly model verbose name. The instance
        # representation is set by model's __str__()
        self.assertContains(
            response,
            '<li class="success">The telegram “<a href="%s">'
            "Telegram without typo</a>” was changed successfully.</li>"
            % reverse("admin:admin_views_telegram_change", args=(t.pk,)),
            html=True,
        )

        # model has no __str__ method
        p = Paper.objects.create(title="My Paper Title")
        self.assertEqual(Paper.objects.count(), 1)
        response = self.client.get(
            reverse("admin:admin_views_paper_change", args=(p.pk,))
        )
        self.assertEqual(response.status_code, 200)
        # Emulate model instance edit via the admin
        post_data = {
            "title": "My Modified Paper Title",
            "_save": "Save",
        }
        response = self.client.post(
            reverse("admin:admin_views_paper_change", args=(p.pk,)),
            post_data,
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Paper.objects.count(), 1)
        # Message should contain non-ugly model verbose name. The ugly(!)
        # instance representation is set by __str__().
        self.assertContains(
            response,
            '<li class="success">The paper “<a href="%s">'
            "%s</a>” was changed successfully.</li>"
            % (reverse("admin:admin_views_paper_change", args=(p.pk,)), p),
            html=True,
        )