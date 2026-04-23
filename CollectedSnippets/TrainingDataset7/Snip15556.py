def setUpTestData(cls):
        cls.user = User.objects.create_user(
            "testing", password="password", is_staff=True
        )
        cls.user.user_permissions.add(
            Permission.objects.get(
                codename="view_poll",
                content_type=ContentType.objects.get_for_model(Poll),
            )
        )
        cls.user.user_permissions.add(
            *Permission.objects.filter(
                codename__endswith="question",
                content_type=ContentType.objects.get_for_model(Question),
            ).values_list("pk", flat=True)
        )

        cls.poll = Poll.objects.create(name="Survey")
        cls.add_url = reverse("admin:admin_inlines_poll_add")
        cls.change_url = reverse("admin:admin_inlines_poll_change", args=(cls.poll.id,))