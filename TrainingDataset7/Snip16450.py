def test_protected(self):
        q = Question.objects.create(question="Why?")
        a1 = Answer.objects.create(question=q, answer="Because.")
        a2 = Answer.objects.create(question=q, answer="Yes.")

        response = self.client.get(
            reverse("admin:admin_views_question_delete", args=(q.pk,))
        )
        self.assertContains(
            response, "would require deleting the following protected related objects"
        )
        self.assertContains(
            response,
            '<li>Answer: <a href="%s">Because.</a></li>'
            % reverse("admin:admin_views_answer_change", args=(a1.pk,)),
        )
        self.assertContains(
            response,
            '<li>Answer: <a href="%s">Yes.</a></li>'
            % reverse("admin:admin_views_answer_change", args=(a2.pk,)),
        )