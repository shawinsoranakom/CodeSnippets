def setUpTestData(cls):
        cls.u1 = CustomUserCompositePrimaryKey.custom_objects.create(
            email="staffmember@example.com",
            date_of_birth=datetime.date(1976, 11, 8),
        )
        cls.u1.set_password("password")
        cls.u1.save()