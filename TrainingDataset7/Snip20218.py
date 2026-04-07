def test_removal_through_default_gfk_related_manager(self, bulk=True):
        bugs = FunPerson.objects.create(
            first_name="Bugs", last_name="Bunny", fun=True, favorite_thing=self.b1
        )
        droopy = FunPerson.objects.create(
            first_name="Droopy", last_name="Dog", fun=False, favorite_thing=self.b1
        )

        self.b1.fun_people_favorite_things.remove(droopy, bulk=bulk)
        self.assertQuerySetEqual(
            FunPerson._base_manager.order_by("first_name").filter(
                favorite_thing_id=self.b1.pk
            ),
            [
                "Bugs",
                "Droopy",
            ],
            lambda c: c.first_name,
            ordered=False,
        )

        self.b1.fun_people_favorite_things.remove(bugs, bulk=bulk)
        self.assertQuerySetEqual(
            FunPerson._base_manager.order_by("first_name").filter(
                favorite_thing_id=self.b1.pk
            ),
            [
                "Droopy",
            ],
            lambda c: c.first_name,
            ordered=False,
        )
        bugs.favorite_book = self.b1
        bugs.save()

        self.b1.fun_people_favorite_things.clear(bulk=bulk)
        self.assertQuerySetEqual(
            FunPerson._base_manager.order_by("first_name").filter(
                favorite_thing_id=self.b1.pk
            ),
            [
                "Droopy",
            ],
            lambda c: c.first_name,
            ordered=False,
        )