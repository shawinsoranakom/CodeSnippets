def test_tabular_inline_show_change_link_false_registered(self):
        "Inlines `show_change_link` disabled by default."
        poll = Poll.objects.create(name="New poll")
        Question.objects.create(poll=poll)
        response = self.client.get(
            reverse("admin:admin_inlines_poll_change", args=(poll.pk,))
        )
        self.assertTrue(
            response.context["inline_admin_formset"].opts.has_registered_model
        )
        self.assertNotContains(response, INLINE_CHANGELINK_HTML)