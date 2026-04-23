def test_staff_member_required_decorator_works_with_argument(self):
        """
        Staff_member_required decorator works with an argument
        (redirect_field_name).
        """
        secure_url = "/test_admin/admin/secure-view2/"
        response = self.client.get(secure_url)
        self.assertRedirects(
            response, "%s?myfield=%s" % (reverse("admin:login"), secure_url)
        )