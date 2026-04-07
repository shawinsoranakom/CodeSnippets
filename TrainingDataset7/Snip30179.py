def test_m2m_join_reuse(self):
        FavoriteAuthors.objects.bulk_create(
            [
                FavoriteAuthors(
                    author=self.author1, likes_author=self.author3, is_active=True
                ),
                FavoriteAuthors(
                    author=self.author1,
                    likes_author=self.author4,
                    is_active=False,
                ),
                FavoriteAuthors(
                    author=self.author2, likes_author=self.author3, is_active=True
                ),
                FavoriteAuthors(
                    author=self.author2, likes_author=self.author4, is_active=True
                ),
            ]
        )
        with self.assertNumQueries(2):
            authors = list(
                Author.objects.filter(
                    pk__in=[self.author1.pk, self.author2.pk]
                ).prefetch_related(
                    Prefetch(
                        "favorite_authors",
                        queryset=(
                            Author.objects.annotate(
                                active_favorite=F("likes_me__is_active"),
                            ).filter(active_favorite=True)
                        ),
                        to_attr="active_favorite_authors",
                    )
                )
            )
        self.assertEqual(authors[0].active_favorite_authors, [self.author3])
        self.assertEqual(
            authors[1].active_favorite_authors, [self.author3, self.author4]
        )