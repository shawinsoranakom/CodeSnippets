def test_m2m_related_manager(self):
        bugs = Person.objects.create(first_name="Bugs", last_name="Bunny", fun=True)
        self.b1.authors.add(bugs)
        droopy = Person.objects.create(first_name="Droopy", last_name="Dog", fun=False)
        self.b1.authors.add(droopy)
        bugs = FunPerson.objects.create(first_name="Bugs", last_name="Bunny", fun=True)
        self.b1.fun_authors.add(bugs)
        droopy = FunPerson.objects.create(
            first_name="Droopy", last_name="Dog", fun=False
        )
        self.b1.fun_authors.add(droopy)

        self.assertQuerySetEqual(
            self.b1.authors.order_by("first_name").all(),
            [
                "Bugs",
                "Droopy",
            ],
            lambda c: c.first_name,
            ordered=False,
        )
        self.assertQuerySetEqual(
            self.b1.fun_authors.order_by("first_name").all(),
            [
                "Bugs",
            ],
            lambda c: c.first_name,
            ordered=False,
        )
        self.assertQuerySetEqual(
            self.b1.authors(manager="boring_people").all(),
            [
                "Droopy",
            ],
            lambda c: c.first_name,
            ordered=False,
        )
        self.assertQuerySetEqual(
            self.b1.authors(manager="fun_people").all(),
            [
                "Bugs",
            ],
            lambda c: c.first_name,
            ordered=False,
        )