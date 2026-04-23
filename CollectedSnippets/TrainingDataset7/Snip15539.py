def setUpTestData(cls):
        cls.user = User(username="admin", is_staff=True, is_active=True)
        cls.user.set_password("secret")
        cls.user.save()

        cls.author_ct = ContentType.objects.get_for_model(Author)
        cls.holder_ct = ContentType.objects.get_for_model(Holder2)
        cls.book_ct = ContentType.objects.get_for_model(Book)
        cls.inner_ct = ContentType.objects.get_for_model(Inner2)

        # User always has permissions to add and change Authors, and Holders,
        # the main (parent) models of the inlines. Permissions on the inlines
        # vary per test.
        permission = Permission.objects.get(
            codename="add_author", content_type=cls.author_ct
        )
        cls.user.user_permissions.add(permission)
        permission = Permission.objects.get(
            codename="change_author", content_type=cls.author_ct
        )
        cls.user.user_permissions.add(permission)
        permission = Permission.objects.get(
            codename="add_holder2", content_type=cls.holder_ct
        )
        cls.user.user_permissions.add(permission)
        permission = Permission.objects.get(
            codename="change_holder2", content_type=cls.holder_ct
        )
        cls.user.user_permissions.add(permission)

        author = Author.objects.create(pk=1, name="The Author")
        cls.book = author.books.create(name="The inline Book")
        cls.author_change_url = reverse(
            "admin:admin_inlines_author_change", args=(author.id,)
        )
        # Get the ID of the automatically created intermediate model for the
        # Author-Book m2m.
        author_book_auto_m2m_intermediate = Author.books.through.objects.get(
            author=author, book=cls.book
        )
        cls.author_book_auto_m2m_intermediate_id = author_book_auto_m2m_intermediate.pk

        cls.holder = Holder2.objects.create(dummy=13)
        cls.inner2 = Inner2.objects.create(dummy=42, holder=cls.holder)