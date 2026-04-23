def test_change_password_template_helptext_no_id(self):
        user = User.objects.get(username="super")

        class EmptyIdForLabelTextInput(forms.TextInput):
            def id_for_label(self, id):
                return None

        class EmptyIdForLabelHelpTextPasswordChangeForm(AdminPasswordChangeForm):
            password1 = forms.CharField(
                help_text="Your new password", widget=EmptyIdForLabelTextInput()
            )

        class CustomUserAdmin(UserAdmin):
            change_password_form = EmptyIdForLabelHelpTextPasswordChangeForm

        request = RequestFactory().get(
            reverse("admin:auth_user_password_change", args=(user.id,))
        )
        request.user = user
        user_admin = CustomUserAdmin(User, site)
        response = user_admin.user_change_password(request, str(user.pk))
        self.assertContains(response, '<div class="help">')