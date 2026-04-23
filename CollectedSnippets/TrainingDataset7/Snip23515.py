def test_queries_content_type_restriction(self):
        """
        Create another fatty tagged instance with different PK to ensure there
        is a content type restriction in the generated queries below.
        """
        mpk = ManualPK.objects.create(id=self.lion.pk)
        mpk.tags.create(tag="fatty")
        self.platypus.tags.create(tag="fatty")

        self.assertSequenceEqual(
            Animal.objects.filter(tags__tag="fatty"),
            [self.platypus],
        )
        self.assertSequenceEqual(
            Animal.objects.exclude(tags__tag="fatty"),
            [self.lion],
        )