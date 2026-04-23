def test_m2m(self):
        with self.assertNumQueries(3):
            qs = Author.objects.prefetch_related("favorite_authors", "favors_me")
            favorites = [
                (
                    [str(i_like) for i_like in author.favorite_authors.all()],
                    [str(likes_me) for likes_me in author.favors_me.all()],
                )
                for author in qs
            ]
            self.assertEqual(
                favorites,
                [
                    ([str(self.author2)], [str(self.author3)]),
                    ([str(self.author3)], [str(self.author1)]),
                    ([str(self.author1)], [str(self.author2)]),
                ],
            )