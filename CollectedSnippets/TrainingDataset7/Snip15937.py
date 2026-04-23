def test_hook_get_log_entries(self):
        LogEntry.objects.log_actions(
            self.user.pk,
            [self.a1],
            CHANGE,
            change_message="Article changed message",
        )
        c1 = Car.objects.create()
        LogEntry.objects.log_actions(
            self.user.pk,
            [c1],
            ADDITION,
            change_message="Car created message",
        )
        exp_str_article = escape(str(self.a1))
        exp_str_car = escape(str(c1))

        response = self.client.get(reverse("admin:index"))
        self.assertContains(response, exp_str_article)
        self.assertContains(response, exp_str_car)

        # site "custom_admin" only renders log entries of registered models
        response = self.client.get(reverse("custom_admin:index"))
        self.assertContains(response, exp_str_article)
        self.assertNotContains(response, exp_str_car)