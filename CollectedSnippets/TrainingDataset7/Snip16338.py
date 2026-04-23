def test_date_hierarchy_empty_queryset(self):
        self.assertIs(Question.objects.exists(), False)
        response = self.client.get(reverse("admin:admin_views_answer2_changelist"))
        self.assertEqual(response.status_code, 200)