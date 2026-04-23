def test_alias_with_period_shadows_table_name(self):
        """
        Aliases with periods are not confused for table names from extra().
        """
        Article.objects.update(author=self.author_2)
        Article.objects.create(
            headline="Backdated", pub_date=datetime(1900, 1, 1), author=self.author_1
        )
        crafted = "ordering_article.pub_date"

        qs = Article.objects.annotate(**{crafted: F("author")}).order_by("-" + crafted)
        self.assertNotEqual(qs[0].headline, "Backdated")

        relation = FilteredRelation("author")
        msg = (
            "FilteredRelation doesn't support aliases with periods "
            "(got 'ordering_article.pub_date')."
        )
        with self.assertRaisesMessage(ValueError, msg):
            qs2 = Article.objects.annotate(**{crafted: relation}).order_by(crafted)
            # Before, unlike F(), which causes ordering expressions to be
            # replaced by ordinals like n in ORDER BY n, these were ordered by
            # pub_date instead of author.
            # The Article model orders by -pk, so sorting on author will place
            # first any article by author2 instead of the backdated one.
            # This assertion is reachable if FilteredRelation.__init__() starts
            # supporting periods in aliases in the future.
            self.assertNotEqual(qs2[0].headline, "Backdated")