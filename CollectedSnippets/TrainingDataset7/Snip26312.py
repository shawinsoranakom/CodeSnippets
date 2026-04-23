def test_add(self):
        # Create an Article.
        a5 = Article(headline="Django lets you create web apps easily")
        # You can't associate it with a Publication until it's been saved.
        msg = (
            '"<Article: Django lets you create web apps easily>" needs to have '
            'a value for field "id" before this many-to-many relationship can be used.'
        )
        with self.assertRaisesMessage(ValueError, msg):
            getattr(a5, "publications")
        # Save it!
        a5.save()
        # Associate the Article with a Publication.
        a5.publications.add(self.p1)
        self.assertSequenceEqual(a5.publications.all(), [self.p1])
        # Create another Article, and set it to appear in both Publications.
        a6 = Article(headline="ESA uses Python")
        a6.save()
        a6.publications.add(self.p1, self.p2)
        a6.publications.add(self.p3)
        # Adding a second time is OK
        a6.publications.add(self.p3)
        self.assertSequenceEqual(
            a6.publications.all(),
            [self.p2, self.p3, self.p1],
        )

        # Adding an object of the wrong type raises TypeError
        msg = (
            "'Publication' instance expected, got <Article: Django lets you create web "
            "apps easily>"
        )
        with self.assertRaisesMessage(TypeError, msg):
            with transaction.atomic():
                a6.publications.add(a5)

        # Add a Publication directly via publications.add by using keyword
        # arguments.
        p5 = a6.publications.create(title="Highlights for Adults")
        self.assertSequenceEqual(
            a6.publications.all(),
            [p5, self.p2, self.p3, self.p1],
        )