def test_unique_for_date(self):
        p = Post.objects.create(
            title="Django 1.0 is released",
            slug="Django 1.0",
            subtitle="Finally",
            posted=datetime.date(2008, 9, 3),
        )
        form = PostForm({"title": "Django 1.0 is released", "posted": "2008-09-03"})
        self.assertFalse(form.is_valid())
        self.assertEqual(len(form.errors), 1)
        self.assertEqual(
            form.errors["title"], ["Title must be unique for Posted date."]
        )
        form = PostForm({"title": "Work on Django 1.1 begins", "posted": "2008-09-03"})
        self.assertTrue(form.is_valid())
        form = PostForm({"title": "Django 1.0 is released", "posted": "2008-09-04"})
        self.assertTrue(form.is_valid())
        form = PostForm({"slug": "Django 1.0", "posted": "2008-01-01"})
        self.assertFalse(form.is_valid())
        self.assertEqual(len(form.errors), 1)
        self.assertEqual(form.errors["slug"], ["Slug must be unique for Posted year."])
        form = PostForm({"subtitle": "Finally", "posted": "2008-09-30"})
        self.assertFalse(form.is_valid())
        self.assertEqual(
            form.errors["subtitle"], ["Subtitle must be unique for Posted month."]
        )
        data = {
            "subtitle": "Finally",
            "title": "Django 1.0 is released",
            "slug": "Django 1.0",
            "posted": "2008-09-03",
        }
        form = PostForm(data, instance=p)
        self.assertTrue(form.is_valid())
        form = PostForm({"title": "Django 1.0 is released"})
        self.assertFalse(form.is_valid())
        self.assertEqual(len(form.errors), 1)
        self.assertEqual(form.errors["posted"], ["This field is required."])