def test_abstract_base_class_m2m_relation_inheritance(self):
        # many-to-many relations defined on an abstract base class are
        # correctly inherited (and created) on the child class.
        p1 = Person.objects.create(name="Alice")
        p2 = Person.objects.create(name="Bob")
        p3 = Person.objects.create(name="Carol")
        p4 = Person.objects.create(name="Dave")

        birthday = BirthdayParty.objects.create(name="Birthday party for Alice")
        birthday.attendees.set([p1, p3])

        bachelor = BachelorParty.objects.create(name="Bachelor party for Bob")
        bachelor.attendees.set([p2, p4])

        parties = list(p1.birthdayparty_set.all())
        self.assertEqual(parties, [birthday])

        parties = list(p1.bachelorparty_set.all())
        self.assertEqual(parties, [])

        parties = list(p2.bachelorparty_set.all())
        self.assertEqual(parties, [bachelor])

        # A subclass of a subclass of an abstract model doesn't get its own
        # accessor.
        self.assertFalse(hasattr(p2, "messybachelorparty_set"))

        # ... but it does inherit the m2m from its parent
        messy = MessyBachelorParty.objects.create(name="Bachelor party for Dave")
        messy.attendees.set([p4])
        messy_parent = messy.bachelorparty_ptr

        parties = list(p4.bachelorparty_set.all())
        self.assertEqual(parties, [bachelor, messy_parent])