def test_can_create_instance_using_kwargs(self):
        a = Article(
            id=None,
            headline="Third article",
            pub_date=datetime(2005, 7, 30),
        )
        a.save()
        self.assertEqual(a.headline, "Third article")
        self.assertEqual(a.pub_date, datetime(2005, 7, 30, 0, 0))