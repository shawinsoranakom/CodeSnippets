def test_unique_for_date_in_exclude(self):
        """
        If the date for unique_for_* constraints is excluded from the
        ModelForm (in this case 'posted' has editable=False, then the
        constraint should be ignored.
        """

        class DateTimePostForm(forms.ModelForm):
            class Meta:
                model = DateTimePost
                fields = "__all__"

        DateTimePost.objects.create(
            title="Django 1.0 is released",
            slug="Django 1.0",
            subtitle="Finally",
            posted=datetime.datetime(2008, 9, 3, 10, 10, 1),
        )
        # 'title' has unique_for_date='posted'
        form = DateTimePostForm(
            {"title": "Django 1.0 is released", "posted": "2008-09-03"}
        )
        self.assertTrue(form.is_valid())
        # 'slug' has unique_for_year='posted'
        form = DateTimePostForm({"slug": "Django 1.0", "posted": "2008-01-01"})
        self.assertTrue(form.is_valid())
        # 'subtitle' has unique_for_month='posted'
        form = DateTimePostForm({"subtitle": "Finally", "posted": "2008-09-30"})
        self.assertTrue(form.is_valid())