def test_model_permission_denied(self):
        person_url = reverse(
            "django-admindocs-models-detail", args=["admin_docs", "person"]
        )
        company_url = reverse(
            "django-admindocs-models-detail", args=["admin_docs", "company"]
        )
        staff_user = User.objects.create_user(
            username="staff", password="secret", is_staff=True
        )
        self.client.force_login(staff_user)
        response_for_person = self.client.get(person_url)
        response_for_company = self.client.get(company_url)
        # No access without permissions.
        self.assertEqual(response_for_person.status_code, 403)
        self.assertEqual(response_for_company.status_code, 403)
        company_content_type = ContentType.objects.get_for_model(Company)
        person_content_type = ContentType.objects.get_for_model(Person)
        view_company = Permission.objects.get(
            codename="view_company", content_type=company_content_type
        )
        change_person = Permission.objects.get(
            codename="change_person", content_type=person_content_type
        )
        staff_user.user_permissions.add(view_company, change_person)
        with captured_stderr():
            response_for_person = self.client.get(person_url)
        response_for_company = self.client.get(company_url)
        # View or change permission grants access.
        self.assertEqual(response_for_person.status_code, 200)
        self.assertEqual(response_for_company.status_code, 200)