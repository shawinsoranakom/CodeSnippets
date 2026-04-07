def test_m2m_editing(self):
        self.create_basic_data()
        form_data = {
            "headline": "New headline",
            "slug": "new-headline",
            "pub_date": "1988-01-04",
            "writer": str(self.w_royko.pk),
            "article": "Hello.",
            "categories": [str(self.c1.id), str(self.c2.id)],
        }
        # Create a new article, with categories, via the form.
        f = ArticleForm(form_data)
        new_art = f.save()
        new_art = Article.objects.get(id=new_art.id)
        art_id_1 = new_art.id
        self.assertSequenceEqual(
            new_art.categories.order_by("name"), [self.c1, self.c2]
        )

        # Now, submit form data with no categories. This deletes the existing
        # categories.
        form_data["categories"] = []
        f = ArticleForm(form_data, instance=new_art)
        new_art = f.save()
        self.assertEqual(new_art.id, art_id_1)
        new_art = Article.objects.get(id=art_id_1)
        self.assertSequenceEqual(new_art.categories.all(), [])

        # Create a new article, with no categories, via the form.
        f = ArticleForm(form_data)
        new_art = f.save()
        art_id_2 = new_art.id
        self.assertNotIn(art_id_2, (None, art_id_1))
        new_art = Article.objects.get(id=art_id_2)
        self.assertSequenceEqual(new_art.categories.all(), [])

        # Create a new article, with categories, via the form, but use
        # commit=False. The m2m data won't be saved until save_m2m() is invoked
        # on the form.
        form_data["categories"] = [str(self.c1.id), str(self.c2.id)]
        f = ArticleForm(form_data)
        new_art = f.save(commit=False)

        # Manually save the instance
        new_art.save()
        art_id_3 = new_art.id
        self.assertNotIn(art_id_3, (None, art_id_1, art_id_2))

        # The instance doesn't have m2m data yet
        new_art = Article.objects.get(id=art_id_3)
        self.assertSequenceEqual(new_art.categories.all(), [])

        # Save the m2m data on the form
        f.save_m2m()
        self.assertSequenceEqual(
            new_art.categories.order_by("name"), [self.c1, self.c2]
        )