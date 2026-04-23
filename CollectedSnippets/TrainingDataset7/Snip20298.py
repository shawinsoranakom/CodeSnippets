def test_textfields_str(self):
        """TextField values returned from the database should be str."""
        d = Donut.objects.create(name="Jelly Donut", review="Outstanding")
        newd = Donut.objects.get(id=d.id)
        self.assertIsInstance(newd.review, str)