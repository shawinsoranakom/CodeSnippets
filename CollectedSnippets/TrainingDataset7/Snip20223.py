def test_removal_through_specified_m2m_related_manager(self):
        bugs = Person.objects.create(first_name="Bugs", last_name="Bunny", fun=True)
        self.b1.authors.add(bugs)
        droopy = Person.objects.create(first_name="Droopy", last_name="Dog", fun=False)
        self.b1.authors.add(droopy)

        # The fun manager DOESN'T remove boring people.
        self.b1.authors(manager="fun_people").remove(droopy)
        self.assertQuerySetEqual(
            self.b1.authors(manager="boring_people").all(),
            [
                "Droopy",
            ],
            lambda c: c.first_name,
            ordered=False,
        )

        # The boring manager DOES remove boring people.
        self.b1.authors(manager="boring_people").remove(droopy)
        self.assertQuerySetEqual(
            self.b1.authors(manager="boring_people").all(),
            [],
            lambda c: c.first_name,
            ordered=False,
        )
        self.b1.authors.add(droopy)

        # The fun manager ONLY clears fun people.
        self.b1.authors(manager="fun_people").clear()
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
            [],
            lambda c: c.first_name,
            ordered=False,
        )