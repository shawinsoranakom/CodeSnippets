def test_removal_through_default_m2m_related_manager(self):
        bugs = FunPerson.objects.create(first_name="Bugs", last_name="Bunny", fun=True)
        self.b1.fun_authors.add(bugs)
        droopy = FunPerson.objects.create(
            first_name="Droopy", last_name="Dog", fun=False
        )
        self.b1.fun_authors.add(droopy)

        self.b1.fun_authors.remove(droopy)
        self.assertQuerySetEqual(
            self.b1.fun_authors.through._default_manager.all(),
            [
                "Bugs",
                "Droopy",
            ],
            lambda c: c.funperson.first_name,
            ordered=False,
        )

        self.b1.fun_authors.remove(bugs)
        self.assertQuerySetEqual(
            self.b1.fun_authors.through._default_manager.all(),
            [
                "Droopy",
            ],
            lambda c: c.funperson.first_name,
            ordered=False,
        )
        self.b1.fun_authors.add(bugs)

        self.b1.fun_authors.clear()
        self.assertQuerySetEqual(
            self.b1.fun_authors.through._default_manager.all(),
            [
                "Droopy",
            ],
            lambda c: c.funperson.first_name,
            ordered=False,
        )