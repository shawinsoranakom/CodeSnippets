def test_fk_related_manager(self):
        Person.objects.create(
            first_name="Bugs", last_name="Bunny", fun=True, favorite_book=self.b1
        )
        Person.objects.create(
            first_name="Droopy", last_name="Dog", fun=False, favorite_book=self.b1
        )
        FunPerson.objects.create(
            first_name="Bugs", last_name="Bunny", fun=True, favorite_book=self.b1
        )
        FunPerson.objects.create(
            first_name="Droopy", last_name="Dog", fun=False, favorite_book=self.b1
        )

        self.assertQuerySetEqual(
            self.b1.favorite_books.order_by("first_name").all(),
            [
                "Bugs",
                "Droopy",
            ],
            lambda c: c.first_name,
            ordered=False,
        )
        self.assertQuerySetEqual(
            self.b1.fun_people_favorite_books.all(),
            [
                "Bugs",
            ],
            lambda c: c.first_name,
            ordered=False,
        )
        self.assertQuerySetEqual(
            self.b1.favorite_books(manager="boring_people").all(),
            [
                "Droopy",
            ],
            lambda c: c.first_name,
            ordered=False,
        )
        self.assertQuerySetEqual(
            self.b1.favorite_books(manager="fun_people").all(),
            [
                "Bugs",
            ],
            lambda c: c.first_name,
            ordered=False,
        )