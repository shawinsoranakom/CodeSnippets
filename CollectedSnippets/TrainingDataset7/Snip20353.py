def test_update(self):
        author = Author.objects.create(name="James Smith", goes_by="Jim")
        Author.objects.update(alias=Greatest("name", "goes_by"))
        author.refresh_from_db()
        self.assertEqual(author.alias, "Jim")