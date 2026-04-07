def test_post_delete_protected(self):
        """
        A POST request to delete protected objects should display the page
        which says the deletion is prohibited.
        """
        q = Question.objects.create(question="Why?")
        Answer.objects.create(question=q, answer="Because.")

        response = self.client.post(
            reverse("admin:admin_views_question_delete", args=(q.pk,)), {"post": "yes"}
        )
        self.assertEqual(Question.objects.count(), 1)
        self.assertContains(
            response, "would require deleting the following protected related objects"
        )