def test_initial_values(self):
        self.create_basic_data()
        # Initial values can be provided for model forms
        f = ArticleForm(
            auto_id=False,
            initial={
                "headline": "Your headline here",
                "categories": [str(self.c1.id), str(self.c2.id)],
            },
        )
        self.assertHTMLEqual(
            f.as_ul(),
            """
            <li>Headline:
            <input type="text" name="headline" value="Your headline here" maxlength="50"
                required>
            </li>
            <li>Slug: <input type="text" name="slug" maxlength="50" required></li>
            <li>Pub date: <input type="text" name="pub_date" required></li>
            <li>Writer: <select name="writer" required>
            <option value="" selected>---------</option>
            <option value="%s">Bob Woodward</option>
            <option value="%s">Mike Royko</option>
            </select></li>
            <li>Article:
            <textarea rows="10" cols="40" name="article" required></textarea></li>
            <li>Categories: <select multiple name="categories">
            <option value="%s" selected>Entertainment</option>
            <option value="%s" selected>It&#x27;s a test</option>
            <option value="%s">Third test</option>
            </select></li>
            <li>Status: <select name="status">
            <option value="" selected>---------</option>
            <option value="1">Draft</option>
            <option value="2">Pending</option>
            <option value="3">Live</option>
            </select></li>
            """
            % (self.w_woodward.pk, self.w_royko.pk, self.c1.pk, self.c2.pk, self.c3.pk),
        )

        # When the ModelForm is passed an instance, that instance's current
        # values are inserted as 'initial' data in each Field.
        f = RoykoForm(auto_id=False, instance=self.w_royko)
        self.assertHTMLEqual(
            str(f),
            '<div>Name:<div class="helptext">Use both first and last names.</div>'
            '<input type="text" name="name" value="Mike Royko" maxlength="50" '
            "required></div>",
        )

        art = Article.objects.create(
            headline="Test article",
            slug="test-article",
            pub_date=datetime.date(1988, 1, 4),
            writer=self.w_royko,
            article="Hello.",
        )
        art_id_1 = art.id

        f = ArticleForm(auto_id=False, instance=art)
        self.assertHTMLEqual(
            f.as_ul(),
            """
            <li>Headline:
            <input type="text" name="headline" value="Test article" maxlength="50"
                required>
            </li>
            <li>Slug:
            <input type="text" name="slug" value="test-article" maxlength="50" required>
            </li>
            <li>Pub date:
            <input type="text" name="pub_date" value="1988-01-04" required></li>
            <li>Writer: <select name="writer" required>
            <option value="">---------</option>
            <option value="%s">Bob Woodward</option>
            <option value="%s" selected>Mike Royko</option>
            </select></li>
            <li>Article:
            <textarea rows="10" cols="40" name="article" required>Hello.</textarea></li>
            <li>Categories: <select multiple name="categories">
            <option value="%s">Entertainment</option>
            <option value="%s">It&#x27;s a test</option>
            <option value="%s">Third test</option>
            </select></li>
            <li>Status: <select name="status">
            <option value="" selected>---------</option>
            <option value="1">Draft</option>
            <option value="2">Pending</option>
            <option value="3">Live</option>
            </select></li>
            """
            % (self.w_woodward.pk, self.w_royko.pk, self.c1.pk, self.c2.pk, self.c3.pk),
        )

        f = ArticleForm(
            {
                "headline": "Test headline",
                "slug": "test-headline",
                "pub_date": "1984-02-06",
                "writer": str(self.w_royko.pk),
                "article": "Hello.",
            },
            instance=art,
        )
        self.assertEqual(f.errors, {})
        self.assertTrue(f.is_valid())
        test_art = f.save()
        self.assertEqual(test_art.id, art_id_1)
        test_art = Article.objects.get(id=art_id_1)
        self.assertEqual(test_art.headline, "Test headline")