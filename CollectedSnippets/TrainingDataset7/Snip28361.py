def test_default_selectdatewidget(self):
        class PubForm(forms.ModelForm):
            date_published = forms.DateField(
                required=False, widget=forms.SelectDateWidget
            )

            class Meta:
                model = PublicationDefaults
                fields = ("date_published",)

        mf1 = PubForm({})
        self.assertEqual(mf1.errors, {})
        m1 = mf1.save(commit=False)
        self.assertEqual(m1.date_published, datetime.date.today())

        mf2 = PubForm(
            {
                "date_published_year": "2010",
                "date_published_month": "1",
                "date_published_day": "1",
            }
        )
        self.assertEqual(mf2.errors, {})
        m2 = mf2.save(commit=False)
        self.assertEqual(m2.date_published, datetime.date(2010, 1, 1))