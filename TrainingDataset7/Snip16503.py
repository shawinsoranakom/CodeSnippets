def setUpTestData(cls):
        cls.superuser = User.objects.create_superuser(
            username="super", password="secret", email="super@example.com"
        )
        cls.joepublicuser = User.objects.create_user(
            username="joepublic", password="secret"
        )
        cls.s1 = Section.objects.create(name="Test section")
        cls.a1 = Article.objects.create(
            content="<p>Middle content</p>",
            date=datetime.datetime(2008, 3, 18, 11, 54, 58),
            section=cls.s1,
        )
        cls.a2 = Article.objects.create(
            content="<p>Oldest content</p>",
            date=datetime.datetime(2000, 3, 18, 11, 54, 58),
            section=cls.s1,
        )
        cls.a3 = Article.objects.create(
            content="<p>Newest content</p>",
            date=datetime.datetime(2009, 3, 18, 11, 54, 58),
            section=cls.s1,
        )
        cls.p1 = PrePopulatedPost.objects.create(
            title="A Long Title", published=True, slug="a-long-title"
        )

        cls.per1 = Person.objects.create(name="John Mauchly", gender=1, alive=True)
        cls.per2 = Person.objects.create(name="Grace Hopper", gender=1, alive=False)
        cls.per3 = Person.objects.create(name="Guido van Rossum", gender=1, alive=True)
        Person.objects.create(name="John Doe", gender=1)
        Person.objects.create(name='John O"Hara', gender=1)
        Person.objects.create(name="John O'Hara", gender=1)

        cls.t1 = Recommender.objects.create()
        cls.t2 = Recommendation.objects.create(the_recommender=cls.t1)
        cls.t3 = Recommender.objects.create()
        cls.t4 = Recommendation.objects.create(the_recommender=cls.t3)

        cls.tt1 = TitleTranslation.objects.create(title=cls.t1, text="Bar")
        cls.tt2 = TitleTranslation.objects.create(title=cls.t2, text="Foo")
        cls.tt3 = TitleTranslation.objects.create(title=cls.t3, text="Few")
        cls.tt4 = TitleTranslation.objects.create(title=cls.t4, text="Bas")