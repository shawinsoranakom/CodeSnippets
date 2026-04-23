def test_change_form_renders_correct_null_choice_value(self):
        """
        Regression test for #17911.
        """
        choice = Choice.objects.create(choice=None)
        response = self.client.get(
            reverse("admin:admin_views_choice_change", args=(choice.pk,))
        )
        self.assertContains(
            response, '<div class="readonly">No opinion</div>', html=True
        )