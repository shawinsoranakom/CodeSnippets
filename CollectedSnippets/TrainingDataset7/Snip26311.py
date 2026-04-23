def setUpTestData(cls):
        # Create a couple of Publications.
        cls.p1 = Publication.objects.create(title="The Python Journal")
        cls.p2 = Publication.objects.create(title="Science News")
        cls.p3 = Publication.objects.create(title="Science Weekly")
        cls.p4 = Publication.objects.create(title="Highlights for Children")

        cls.a1 = Article.objects.create(
            headline="Django lets you build web apps easily"
        )
        cls.a1.publications.add(cls.p1)

        cls.a2 = Article.objects.create(headline="NASA uses Python")
        cls.a2.publications.add(cls.p1, cls.p2, cls.p3, cls.p4)

        cls.a3 = Article.objects.create(headline="NASA finds intelligent life on Earth")
        cls.a3.publications.add(cls.p2)

        cls.a4 = Article.objects.create(headline="Oxygen-free diet works wonders")
        cls.a4.publications.add(cls.p2)