def setUpTestData(cls):
        cls.director = Person.objects.create(name="Terry Gilliam / Terry Jones")
        cls.movie = Movie.objects.create(
            title="Monty Python and the Holy Grail", director=cls.director
        )