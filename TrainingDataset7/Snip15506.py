def test_model_error_inline_with_readonly_field(self):
        poll = Poll.objects.create(name="Test poll")
        data = {
            "question_set-TOTAL_FORMS": 1,
            "question_set-INITIAL_FORMS": 0,
            "question_set-MAX_NUM_FORMS": 0,
            "_save": "Save",
            "question_set-0-text": "Question",
            "question_set-0-poll": poll.pk,
        }
        response = self.client.post(
            reverse("admin:admin_inlines_poll_change", args=(poll.pk,)),
            data,
        )
        self.assertContains(response, "Always invalid model.")