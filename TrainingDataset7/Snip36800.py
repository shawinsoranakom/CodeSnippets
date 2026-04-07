def test_unique_for_date(self):
        Post.objects.create(
            title="Django 1.0 is released",
            slug="Django 1.0",
            subtitle="Finally",
            posted=datetime.date(2008, 9, 3),
        )
        p = Post(title="Django 1.0 is released", posted=datetime.date(2008, 9, 3))
        with self.assertRaises(ValidationError) as cm:
            p.full_clean()
        self.assertEqual(
            cm.exception.message_dict,
            {"title": ["Title must be unique for Posted date."]},
        )

        # Should work without errors
        p = Post(title="Work on Django 1.1 begins", posted=datetime.date(2008, 9, 3))
        p.full_clean()

        # Should work without errors
        p = Post(title="Django 1.0 is released", posted=datetime.datetime(2008, 9, 4))
        p.full_clean()

        p = Post(slug="Django 1.0", posted=datetime.datetime(2008, 1, 1))
        with self.assertRaises(ValidationError) as cm:
            p.full_clean()
        self.assertEqual(
            cm.exception.message_dict,
            {"slug": ["Slug must be unique for Posted year."]},
        )

        p = Post(subtitle="Finally", posted=datetime.datetime(2008, 9, 30))
        with self.assertRaises(ValidationError) as cm:
            p.full_clean()
        self.assertEqual(
            cm.exception.message_dict,
            {"subtitle": ["Subtitle must be unique for Posted month."]},
        )

        p = Post(title="Django 1.0 is released")
        with self.assertRaises(ValidationError) as cm:
            p.full_clean()
        self.assertEqual(
            cm.exception.message_dict, {"posted": ["This field cannot be null."]}
        )