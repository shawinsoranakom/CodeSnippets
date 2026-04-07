def test_onetoone_reverse_with_to_field_pk(self):
        """
        A model (Bio) with a OneToOneField primary key (author) that references
        a non-pk field (name) on the related model (Author) is prefetchable.
        """
        Bio.objects.bulk_create(
            [
                Bio(author=self.author1),
                Bio(author=self.author2),
                Bio(author=self.author3),
            ]
        )
        authors = Author.objects.filter(
            name__in=[self.author1, self.author2, self.author3],
        ).prefetch_related("bio")
        with self.assertNumQueries(2):
            for author in authors:
                self.assertEqual(author.name, author.bio.author.name)