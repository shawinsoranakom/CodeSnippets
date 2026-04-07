def test_subset_fields(self):
        # You can restrict a form to a subset of the complete list of fields
        # by providing a 'fields' argument. If you try to save a
        # model created with such a form, you need to ensure that the fields
        # that are _not_ on the form have default values, or are allowed to
        # have a value of None. If a field isn't specified on a form, the
        # object created from the form can't provide a value for that field!
        class PartialArticleForm(forms.ModelForm):
            class Meta:
                model = Article
                fields = ("headline", "pub_date")

        f = PartialArticleForm(auto_id=False)
        self.assertHTMLEqual(
            str(f),
            '<div>Headline:<input type="text" name="headline" maxlength="50" required>'
            '</div><div>Pub date:<input type="text" name="pub_date" required></div>',
        )

        class PartialArticleFormWithSlug(forms.ModelForm):
            class Meta:
                model = Article
                fields = ("headline", "slug", "pub_date")

        w_royko = Writer.objects.create(name="Mike Royko")
        art = Article.objects.create(
            article="Hello.",
            headline="New headline",
            slug="new-headline",
            pub_date=datetime.date(1988, 1, 4),
            writer=w_royko,
        )
        f = PartialArticleFormWithSlug(
            {
                "headline": "New headline",
                "slug": "new-headline",
                "pub_date": "1988-01-04",
            },
            auto_id=False,
            instance=art,
        )
        self.assertHTMLEqual(
            f.as_ul(),
            """
            <li>Headline:
            <input type="text" name="headline" value="New headline" maxlength="50"
                required>
            </li>
            <li>Slug:
            <input type="text" name="slug" value="new-headline" maxlength="50"
                required>
            </li>
            <li>Pub date:
            <input type="text" name="pub_date" value="1988-01-04" required></li>
            """,
        )
        self.assertTrue(f.is_valid())
        new_art = f.save()
        self.assertEqual(new_art.id, art.id)
        new_art = Article.objects.get(id=art.id)
        self.assertEqual(new_art.headline, "New headline")