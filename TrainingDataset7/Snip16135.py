def test_model_admin_default_delete_action_protected(self):
        """
        The default delete action where some related objects are protected
        from deletion.
        """
        q1 = Question.objects.create(question="Why?")
        a1 = Answer.objects.create(question=q1, answer="Because.")
        a2 = Answer.objects.create(question=q1, answer="Yes.")
        q2 = Question.objects.create(question="Wherefore?")
        action_data = {
            ACTION_CHECKBOX_NAME: [q1.pk, q2.pk],
            "action": "delete_selected",
            "index": 0,
        }
        delete_confirmation_data = action_data.copy()
        delete_confirmation_data["post"] = "yes"
        response = self.client.post(
            reverse("admin:admin_views_question_changelist"), action_data
        )
        self.assertContains(
            response, "would require deleting the following protected related objects"
        )
        self.assertContains(
            response,
            '<li>Answer: <a href="%s">Because.</a></li>'
            % reverse("admin:admin_views_answer_change", args=(a1.pk,)),
            html=True,
        )
        self.assertContains(
            response,
            '<li>Answer: <a href="%s">Yes.</a></li>'
            % reverse("admin:admin_views_answer_change", args=(a2.pk,)),
            html=True,
        )
        # A POST request to delete protected objects displays the page which
        # says the deletion is prohibited.
        response = self.client.post(
            reverse("admin:admin_views_question_changelist"), delete_confirmation_data
        )
        self.assertContains(
            response, "would require deleting the following protected related objects"
        )
        self.assertEqual(Question.objects.count(), 2)