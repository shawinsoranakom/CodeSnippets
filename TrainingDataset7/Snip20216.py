def test_removal_through_specified_fk_related_manager(self, bulk=True):
        Person.objects.create(
            first_name="Bugs", last_name="Bunny", fun=True, favorite_book=self.b1
        )
        droopy = Person.objects.create(
            first_name="Droopy", last_name="Dog", fun=False, favorite_book=self.b1
        )

        # The fun manager DOESN'T remove boring people.
        self.b1.favorite_books(manager="fun_people").remove(droopy, bulk=bulk)
        self.assertQuerySetEqual(
            self.b1.favorite_books(manager="boring_people").all(),
            [
                "Droopy",
            ],
            lambda c: c.first_name,
            ordered=False,
        )
        # The boring manager DOES remove boring people.
        self.b1.favorite_books(manager="boring_people").remove(droopy, bulk=bulk)
        self.assertQuerySetEqual(
            self.b1.favorite_books(manager="boring_people").all(),
            [],
            lambda c: c.first_name,
            ordered=False,
        )
        droopy.favorite_book = self.b1
        droopy.save()

        # The fun manager ONLY clears fun people.
        self.b1.favorite_books(manager="fun_people").clear(bulk=bulk)
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
            [],
            lambda c: c.first_name,
            ordered=False,
        )