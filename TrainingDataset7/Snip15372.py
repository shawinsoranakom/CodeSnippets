def test_model_index_with_model_permission(self):
        staff_user = User.objects.create_user(
            username="staff", password="secret", is_staff=True
        )
        self.client.force_login(staff_user)
        index_url = reverse("django-admindocs-models-index")
        response = self.client.get(index_url)
        # Models are not listed without permissions.
        self.assertNotContains(
            response,
            '<a href="/admindocs/models/admin_docs.family/">Family</a>',
            html=True,
        )
        self.assertNotContains(
            response,
            '<a href="/admindocs/models/admin_docs.person/">Person</a>',
            html=True,
        )
        self.assertNotContains(
            response,
            '<a href="/admindocs/models/admin_docs.company/">Company</a>',
            html=True,
        )
        company_content_type = ContentType.objects.get_for_model(Company)
        person_content_type = ContentType.objects.get_for_model(Person)
        view_company = Permission.objects.get(
            codename="view_company", content_type=company_content_type
        )
        change_person = Permission.objects.get(
            codename="change_person", content_type=person_content_type
        )
        staff_user.user_permissions.add(view_company, change_person)
        response = self.client.get(index_url)
        # View or change permission grants access.
        self.assertNotContains(
            response,
            '<a href="/admindocs/models/admin_docs.family/">Family</a>',
            html=True,
        )
        self.assertContains(
            response,
            '<a href="/admindocs/models/admin_docs.person/">Person</a>',
            html=True,
        )
        self.assertContains(
            response,
            '<a href="/admindocs/models/admin_docs.company/">Company</a>',
            html=True,
        )