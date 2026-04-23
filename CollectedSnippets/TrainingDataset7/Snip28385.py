def test_unique_for_date_with_nullable_date(self):
        class FlexDatePostForm(forms.ModelForm):
            class Meta:
                model = FlexibleDatePost
                fields = "__all__"

        p = FlexibleDatePost.objects.create(
            title="Django 1.0 is released",
            slug="Django 1.0",
            subtitle="Finally",
            posted=datetime.date(2008, 9, 3),
        )

        form = FlexDatePostForm({"title": "Django 1.0 is released"})
        self.assertTrue(form.is_valid())
        form = FlexDatePostForm({"slug": "Django 1.0"})
        self.assertTrue(form.is_valid())
        form = FlexDatePostForm({"subtitle": "Finally"})
        self.assertTrue(form.is_valid())
        data = {
            "subtitle": "Finally",
            "title": "Django 1.0 is released",
            "slug": "Django 1.0",
        }
        form = FlexDatePostForm(data, instance=p)
        self.assertTrue(form.is_valid())