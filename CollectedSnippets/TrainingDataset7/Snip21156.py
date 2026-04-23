def test_generic_relation_cascade(self):
        """
        Django cascades deletes through generic-related objects to their
        reverse relations.
        """
        person = Person.objects.create(name="Nelson Mandela")
        award = Award.objects.create(name="Nobel", content_object=person)
        AwardNote.objects.create(note="a peace prize", award=award)
        self.assertEqual(AwardNote.objects.count(), 1)
        person.delete()
        self.assertEqual(Award.objects.count(), 0)
        # first two asserts are just sanity checks, this is the kicker:
        self.assertEqual(AwardNote.objects.count(), 0)