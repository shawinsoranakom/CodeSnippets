def test_removal_through_default_fk_related_manager(self, bulk=True):
        bugs = FunPerson.objects.create(
            first_name="Bugs", last_name="Bunny", fun=True, favorite_book=self.b1
        )
        droopy = FunPerson.objects.create(
            first_name="Droopy", last_name="Dog", fun=False, favorite_book=self.b1
        )

        self.b1.fun_people_favorite_books.remove(droopy, bulk=bulk)
        self.assertQuerySetEqual(
            FunPerson._base_manager.filter(favorite_book=self.b1),
            [
                "Bugs",
                "Droopy",
            ],
            lambda c: c.first_name,
            ordered=False,
        )

        self.b1.fun_people_favorite_books.remove(bugs, bulk=bulk)
        self.assertQuerySetEqual(
            FunPerson._base_manager.filter(favorite_book=self.b1),
            [
                "Droopy",
            ],
            lambda c: c.first_name,
            ordered=False,
        )
        bugs.favorite_book = self.b1
        bugs.save()

        self.b1.fun_people_favorite_books.clear(bulk=bulk)
        self.assertQuerySetEqual(
            FunPerson._base_manager.filter(favorite_book=self.b1),
            [
                "Droopy",
            ],
            lambda c: c.first_name,
            ordered=False,
        )