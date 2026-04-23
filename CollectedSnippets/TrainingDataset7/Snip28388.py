def test_override_unique_for_date_message(self):
        class CustomPostForm(PostForm):
            class Meta(PostForm.Meta):
                error_messages = {
                    "title": {
                        "unique_for_date": (
                            "%(model_name)s's %(field_label)s not unique "
                            "for %(date_field_label)s date."
                        ),
                    }
                }

        Post.objects.create(
            title="Django 1.0 is released",
            slug="Django 1.0",
            subtitle="Finally",
            posted=datetime.date(2008, 9, 3),
        )
        form = CustomPostForm(
            {"title": "Django 1.0 is released", "posted": "2008-09-03"}
        )
        self.assertEqual(len(form.errors), 1)
        self.assertEqual(
            form.errors["title"], ["Post's Title not unique for Posted date."]
        )