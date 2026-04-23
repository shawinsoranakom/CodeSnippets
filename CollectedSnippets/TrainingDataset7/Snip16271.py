def setUpTestData(cls):
        cls.superuser = User.objects.create_superuser(
            username="super", password="secret", email="super@example.com"
        )
        cls.s1 = Section.objects.create(name="Test section")
        cls.a1 = Article.objects.create(
            content="<p>Middle content</p>",
            date=datetime.datetime(2008, 3, 18, 11, 54, 58),
            section=cls.s1,
            title="Article 1",
        )
        cls.a2 = Article.objects.create(
            content="<p>Oldest content</p>",
            date=datetime.datetime(2000, 3, 18, 11, 54, 58),
            section=cls.s1,
            title="Article 2",
        )
        cls.a3 = Article.objects.create(
            content="<p>Newest content</p>",
            date=datetime.datetime(2009, 3, 18, 11, 54, 58),
            section=cls.s1,
        )
        cls.p1 = PrePopulatedPost.objects.create(
            title="A Long Title", published=True, slug="a-long-title"
        )
        cls.color1 = Color.objects.create(value="Red", warm=True)
        cls.color2 = Color.objects.create(value="Orange", warm=True)
        cls.color3 = Color.objects.create(value="Blue", warm=False)
        cls.color4 = Color.objects.create(value="Green", warm=False)
        cls.fab1 = Fabric.objects.create(surface="x")
        cls.fab2 = Fabric.objects.create(surface="y")
        cls.fab3 = Fabric.objects.create(surface="plain")
        cls.b1 = Book.objects.create(name="Book 1")
        cls.b2 = Book.objects.create(name="Book 2")
        cls.pro1 = Promo.objects.create(name="Promo 1", book=cls.b1)
        cls.pro1 = Promo.objects.create(name="Promo 2", book=cls.b2)
        cls.chap1 = Chapter.objects.create(
            title="Chapter 1", content="[ insert contents here ]", book=cls.b1
        )
        cls.chap2 = Chapter.objects.create(
            title="Chapter 2", content="[ insert contents here ]", book=cls.b1
        )
        cls.chap3 = Chapter.objects.create(
            title="Chapter 1", content="[ insert contents here ]", book=cls.b2
        )
        cls.chap4 = Chapter.objects.create(
            title="Chapter 2", content="[ insert contents here ]", book=cls.b2
        )
        cls.cx1 = ChapterXtra1.objects.create(chap=cls.chap1, xtra="ChapterXtra1 1")
        cls.cx2 = ChapterXtra1.objects.create(chap=cls.chap3, xtra="ChapterXtra1 2")
        Actor.objects.create(name="Palin", age=27)

        # Post data for edit inline
        cls.inline_post_data = {
            "name": "Test section",
            # inline data
            "article_set-TOTAL_FORMS": "6",
            "article_set-INITIAL_FORMS": "3",
            "article_set-MAX_NUM_FORMS": "0",
            "article_set-0-id": cls.a1.pk,
            # there is no title in database, give one here or formset will
            # fail.
            "article_set-0-title": "Norske bostaver æøå skaper problemer",
            "article_set-0-content": "&lt;p&gt;Middle content&lt;/p&gt;",
            "article_set-0-date_0": "2008-03-18",
            "article_set-0-date_1": "11:54:58",
            "article_set-0-section": cls.s1.pk,
            "article_set-1-id": cls.a2.pk,
            "article_set-1-title": "Need a title.",
            "article_set-1-content": "&lt;p&gt;Oldest content&lt;/p&gt;",
            "article_set-1-date_0": "2000-03-18",
            "article_set-1-date_1": "11:54:58",
            "article_set-2-id": cls.a3.pk,
            "article_set-2-title": "Need a title.",
            "article_set-2-content": "&lt;p&gt;Newest content&lt;/p&gt;",
            "article_set-2-date_0": "2009-03-18",
            "article_set-2-date_1": "11:54:58",
            "article_set-3-id": "",
            "article_set-3-title": "",
            "article_set-3-content": "",
            "article_set-3-date_0": "",
            "article_set-3-date_1": "",
            "article_set-4-id": "",
            "article_set-4-title": "",
            "article_set-4-content": "",
            "article_set-4-date_0": "",
            "article_set-4-date_1": "",
            "article_set-5-id": "",
            "article_set-5-title": "",
            "article_set-5-content": "",
            "article_set-5-date_0": "",
            "article_set-5-date_1": "",
        }