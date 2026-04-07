def setUpTestData(cls):
        cls.superuser = User.objects.create_superuser(
            username="super", password="secret", email="super@example.com"
        )
        file1 = tempfile.NamedTemporaryFile(suffix=".file1")
        file1.write(b"a" * (2**21))
        filename = file1.name
        file1.close()
        cls.gallery = Gallery.objects.create(name="Test Gallery")
        cls.picture = Picture.objects.create(
            name="Test Picture",
            image=filename,
            gallery=cls.gallery,
        )