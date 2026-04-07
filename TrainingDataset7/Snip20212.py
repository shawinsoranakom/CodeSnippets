def test_gfk_related_manager(self):
        Person.objects.create(
            first_name="Bugs", last_name="Bunny", fun=True, favorite_thing=self.b1
        )
        Person.objects.create(
            first_name="Droopy", last_name="Dog", fun=False, favorite_thing=self.b1
        )
        FunPerson.objects.create(
            first_name="Bugs", last_name="Bunny", fun=True, favorite_thing=self.b1
        )
        FunPerson.objects.create(
            first_name="Droopy", last_name="Dog", fun=False, favorite_thing=self.b1
        )

        self.assertQuerySetEqual(
            self.b1.favorite_things.all(),
            [
                "Bugs",
                "Droopy",
            ],
            lambda c: c.first_name,
            ordered=False,
        )
        self.assertQuerySetEqual(
            self.b1.fun_people_favorite_things.all(),
            [
                "Bugs",
            ],
            lambda c: c.first_name,
            ordered=False,
        )
        self.assertQuerySetEqual(
            self.b1.favorite_things(manager="boring_people").all(),
            [
                "Droopy",
            ],
            lambda c: c.first_name,
            ordered=False,
        )
        self.assertQuerySetEqual(
            self.b1.favorite_things(manager="fun_people").all(),
            [
                "Bugs",
            ],
            lambda c: c.first_name,
            ordered=False,
        )