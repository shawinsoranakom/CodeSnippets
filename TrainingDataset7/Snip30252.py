def test_retrieves_results_from_prefetched_objects_cache(self):
        """
        When intermediary results are prefetched without a destination
        attribute, they are saved in the RelatedManager's cache
        (_prefetched_objects_cache). prefetch_related() uses this cache
        (#27554).
        """
        authors = AuthorWithAge.objects.prefetch_related(
            Prefetch(
                "author",
                queryset=Author.objects.prefetch_related(
                    # Results are saved in the RelatedManager's cache
                    # (_prefetched_objects_cache) and do not replace the
                    # RelatedManager on Author instances (favorite_authors)
                    Prefetch("favorite_authors__first_book"),
                ),
            ),
        )
        with self.assertNumQueries(4):
            # AuthorWithAge -> Author -> FavoriteAuthors, Book
            self.assertSequenceEqual(authors, [self.author1, self.author2])