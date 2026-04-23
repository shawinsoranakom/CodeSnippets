def setUpTestData(cls):
        cls.superuser = User.objects.create_superuser(
            username="super", password="secret", email="super@example.com"
        )
        cls.deleteuser = User.objects.create_user(
            username="deleteuser", password="secret", is_staff=True
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

        cls.v1 = Villain.objects.create(name="Adam")
        cls.v2 = Villain.objects.create(name="Sue")
        cls.sv1 = SuperVillain.objects.create(name="Bob")
        cls.pl1 = Plot.objects.create(
            name="World Domination", team_leader=cls.v1, contact=cls.v2
        )
        cls.pl2 = Plot.objects.create(
            name="World Peace", team_leader=cls.v2, contact=cls.v2
        )
        cls.pl3 = Plot.objects.create(
            name="Corn Conspiracy", team_leader=cls.v1, contact=cls.v1
        )
        cls.pd1 = PlotDetails.objects.create(details="almost finished", plot=cls.pl1)
        cls.sh1 = SecretHideout.objects.create(
            location="underground bunker", villain=cls.v1
        )
        cls.sh2 = SecretHideout.objects.create(
            location="floating castle", villain=cls.sv1
        )
        cls.ssh1 = SuperSecretHideout.objects.create(
            location="super floating castle!", supervillain=cls.sv1
        )
        cls.cy1 = CyclicOne.objects.create(pk=1, name="I am recursive", two_id=1)
        cls.cy2 = CyclicTwo.objects.create(pk=1, name="I am recursive too", one_id=1)