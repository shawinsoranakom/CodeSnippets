def test_using_is_honored_inheritance(self):
        B = BookWithYear.objects.using("other")
        A = AuthorWithAge.objects.using("other")
        book1 = B.create(title="Poems", published_year=2010)
        B.create(title="More poems", published_year=2011)
        A.create(name="Jane", first_book=book1, age=50)
        A.create(name="Tom", first_book=book1, age=49)

        # parent link
        with self.assertNumQueries(2, using="other"):
            authors = ", ".join(a.author.name for a in A.prefetch_related("author"))

        self.assertEqual(authors, "Jane, Tom")

        # child link
        with self.assertNumQueries(2, using="other"):
            ages = ", ".join(
                str(a.authorwithage.age) for a in A.prefetch_related("authorwithage")
            )

        self.assertEqual(ages, "50, 49")