def setUpTestData(cls):
        cls.superuser = AuthUser.objects.create(is_superuser=True, is_staff=True)
        cls.tu1 = ProxyTrackerUser.objects.create(name="Django Pony", status="emperor")
        cls.i1 = Issue.objects.create(summary="Pony's Issue", assignee=cls.tu1)