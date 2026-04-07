def test_callable_lookup(self):
        """
        Admin inline should invoke local callable when its name is listed in
        readonly_fields.
        """
        response = self.client.get(reverse("admin:admin_inlines_poll_add"))
        # Add parent object view should have the child inlines section
        self.assertContains(
            response,
            '<div class="js-inline-admin-formset inline-group" id="question_set-group"',
        )
        # The right callable should be used for the inline readonly_fields
        # column cells
        self.assertContains(response, "<p>Callable in QuestionInline</p>")