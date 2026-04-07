def test_passwords_marked_as_sensitive_in_admin_forms(self):
        data = {
            "password1": "passwordsensitive",
            "password2": "sensitivepassword",
            "usable_password": "true",
        }
        forms = [
            AdminUserCreationForm({**data, "username": "newusername"}),
            AdminPasswordChangeForm(self.u1, data),
        ]

        password1_fragment = """
         <td>password1</td>
         <td class="code"><pre>&#x27;********************&#x27;</pre></td>
         """
        password2_fragment = """
         <td>password2</td>
         <td class="code"><pre>&#x27;********************&#x27;</pre></td>
        """
        error = ValueError("Forced error")
        for form in forms:
            with self.subTest(form=form):
                with mock.patch.object(
                    SetPasswordMixin, "validate_passwords", side_effect=error
                ):
                    try:
                        form.is_valid()
                    except ValueError:
                        exc_info = sys.exc_info()
                    else:
                        self.fail("Form validation should have failed.")

                response = technical_500_response(RequestFactory().get("/"), *exc_info)

                self.assertNotContains(response, "sensitivepassword", status_code=500)
                self.assertNotContains(response, "passwordsensitive", status_code=500)
                self.assertContains(response, str(error), status_code=500)
                self.assertContains(
                    response, password1_fragment, html=True, status_code=500
                )
                self.assertContains(
                    response, password2_fragment, html=True, status_code=500
                )