def test_regression_8106(self):
        """
        Regression test for bug #8106.

        Same sort of problem as the previous test, but this time there are
        more extra tables to pull in as part of the select_related() and some
        of them could potentially clash (so need to be kept separate).
        """

        us = TUser.objects.create(name="std")
        usp = Person.objects.create(user=us)
        uo = TUser.objects.create(name="org")
        uop = Person.objects.create(user=uo)
        s = Student.objects.create(person=usp)
        o = Organizer.objects.create(person=uop)
        c = Class.objects.create(org=o)
        Enrollment.objects.create(std=s, cls=c)

        e_related = Enrollment.objects.select_related()[0]
        self.assertEqual(e_related.std.person.user.name, "std")
        self.assertEqual(e_related.cls.org.person.user.name, "org")