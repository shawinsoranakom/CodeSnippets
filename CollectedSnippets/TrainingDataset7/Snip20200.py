def setUpTestData(cls):
        cls.b1 = Book.published_objects.create(
            title="How to program", author="Rodney Dangerfield", is_published=True
        )
        cls.b2 = Book.published_objects.create(
            title="How to be smart", author="Albert Einstein", is_published=False
        )

        cls.p1 = Person.objects.create(first_name="Bugs", last_name="Bunny", fun=True)
        cls.droopy = Person.objects.create(
            first_name="Droopy", last_name="Dog", fun=False
        )