def test_multi_fields(self):
        self.create_basic_data()
        self.maxDiff = None
        # ManyToManyFields are represented by a MultipleChoiceField,
        # ForeignKeys and any fields with the 'choices' attribute are
        # represented by a ChoiceField.
        f = ArticleForm(auto_id=False)
        self.assertHTMLEqual(
            str(f),
            """
            <div>Headline:
                <input type="text" name="headline" maxlength="50" required>
            </div>
            <div>Slug:
                <input type="text" name="slug" maxlength="50" required>
            </div>
            <div>Pub date:
                <input type="text" name="pub_date" required>
            </div>
            <div>Writer:
                <select name="writer" required>
                    <option value="" selected>---------</option>
                    <option value="%s">Bob Woodward</option>
                    <option value="%s">Mike Royko</option>
                </select>
            </div>
            <div>Article:
                <textarea name="article" cols="40" rows="10" required></textarea>
            </div>
            <div>Categories:
                <select name="categories" multiple>
                    <option value="%s">Entertainment</option>
                    <option value="%s">It&#x27;s a test</option>
                    <option value="%s">Third test</option>
                </select>
            </div>
            <div>Status:
                <select name="status">
                    <option value="" selected>---------</option>
                    <option value="1">Draft</option><option value="2">Pending</option>
                    <option value="3">Live</option>
                </select>
            </div>
            """
            % (self.w_woodward.pk, self.w_royko.pk, self.c1.pk, self.c2.pk, self.c3.pk),
        )

        # Add some categories and test the many-to-many form output.
        new_art = Article.objects.create(
            article="Hello.",
            headline="New headline",
            slug="new-headline",
            pub_date=datetime.date(1988, 1, 4),
            writer=self.w_royko,
        )
        new_art.categories.add(Category.objects.get(name="Entertainment"))
        self.assertSequenceEqual(new_art.categories.all(), [self.c1])
        f = ArticleForm(auto_id=False, instance=new_art)
        self.assertHTMLEqual(
            f.as_ul(),
            """
            <li>Headline:
            <input type="text" name="headline" value="New headline" maxlength="50"
                required>
            </li>
            <li>Slug:
            <input type="text" name="slug" value="new-headline" maxlength="50" required>
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
            <option value="%s" selected>Entertainment</option>
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