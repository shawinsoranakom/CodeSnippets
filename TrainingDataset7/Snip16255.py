def test_submit_row(self):
        """
        submit_row template tag should pass whole context.
        """
        request = self.request_factory.get(
            reverse("admin:auth_user_change", args=[self.superuser.pk])
        )
        request.user = self.superuser
        admin = UserAdmin(User, site)
        extra_context = {"extra": True}
        response = admin.change_view(
            request, str(self.superuser.pk), extra_context=extra_context
        )
        template_context = submit_row(response.context_data)
        self.assertIs(template_context["extra"], True)
        self.assertIs(template_context["show_save"], True)