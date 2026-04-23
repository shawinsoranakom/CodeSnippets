def setUp(self):
        """
        Create proxy permissions with content_type to the concrete model
        rather than the proxy model (as they were before Django 2.2 and
        migration 11).
        """
        Permission.objects.all().delete()
        self.concrete_content_type = ContentType.objects.get_for_model(Proxy)
        self.default_permission = Permission.objects.create(
            content_type=self.concrete_content_type,
            codename="add_proxy",
            name="Can add proxy",
        )
        self.custom_permission = Permission.objects.create(
            content_type=self.concrete_content_type,
            codename="display_proxys",
            name="May display proxys information",
        )