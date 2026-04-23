def setUpTestData(cls):
        super().setUpTestData()
        cls.holder = Holder.objects.create(dummy=13)
        Inner.objects.create(dummy=42, holder=cls.holder)

        cls.parent = SomeParentModel.objects.create(name="a")
        SomeChildModel.objects.create(name="b", position="0", parent=cls.parent)
        SomeChildModel.objects.create(name="c", position="1", parent=cls.parent)

        cls.view_only_user = User.objects.create_user(
            username="user",
            password="pwd",
            is_staff=True,
        )
        parent_ct = ContentType.objects.get_for_model(SomeParentModel)
        child_ct = ContentType.objects.get_for_model(SomeChildModel)
        permission = Permission.objects.get(
            codename="view_someparentmodel",
            content_type=parent_ct,
        )
        cls.view_only_user.user_permissions.add(permission)
        permission = Permission.objects.get(
            codename="view_somechildmodel",
            content_type=child_ct,
        )
        cls.view_only_user.user_permissions.add(permission)