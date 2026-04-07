def setUpTestData(cls):
        cls.superuser = User.objects.create_superuser(
            username="super", password="secret", email="super@example.com"
        )
        Action.objects.create(name="delete", description="Remove things.")
        Action.objects.create(name="rename", description="Gives things other names.")
        Action.objects.create(name="add", description="Add things.")
        Action.objects.create(
            name="path/to/file/", description="An action with '/' in its name."
        )
        Action.objects.create(
            name="path/to/html/document.html",
            description="An action with a name similar to a HTML doc path.",
        )
        Action.objects.create(
            name="javascript:alert('Hello world');\">Click here</a>",
            description="An action with a name suspected of being a XSS attempt",
        )