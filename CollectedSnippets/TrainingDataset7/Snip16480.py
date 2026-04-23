def setUpTestData(cls):
        cls.superuser = User.objects.create_superuser(
            username="super", password="secret", email="super@example.com"
        )
        cls.b1 = Book.objects.create(name="Lærdommer")
        cls.p1 = Promo.objects.create(name="<Promo for Lærdommer>", book=cls.b1)
        cls.chap1 = Chapter.objects.create(
            title="Norske bostaver æøå skaper problemer",
            content="<p>Svært frustrerende med UnicodeDecodeErro</p>",
            book=cls.b1,
        )
        cls.chap2 = Chapter.objects.create(
            title="Kjærlighet",
            content="<p>La kjærligheten til de lidende seire.</p>",
            book=cls.b1,
        )
        cls.chap3 = Chapter.objects.create(
            title="Kjærlighet", content="<p>Noe innhold</p>", book=cls.b1
        )
        cls.chap4 = ChapterXtra1.objects.create(
            chap=cls.chap1, xtra="<Xtra(1) Norske bostaver æøå skaper problemer>"
        )
        cls.chap5 = ChapterXtra1.objects.create(
            chap=cls.chap2, xtra="<Xtra(1) Kjærlighet>"
        )
        cls.chap6 = ChapterXtra1.objects.create(
            chap=cls.chap3, xtra="<Xtra(1) Kjærlighet>"
        )
        cls.chap7 = ChapterXtra2.objects.create(
            chap=cls.chap1, xtra="<Xtra(2) Norske bostaver æøå skaper problemer>"
        )
        cls.chap8 = ChapterXtra2.objects.create(
            chap=cls.chap2, xtra="<Xtra(2) Kjærlighet>"
        )
        cls.chap9 = ChapterXtra2.objects.create(
            chap=cls.chap3, xtra="<Xtra(2) Kjærlighet>"
        )