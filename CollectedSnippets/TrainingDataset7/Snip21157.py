def test_fk_to_m2m_through(self):
        """
        If an M2M relationship has an explicitly-specified through model, and
        some other model has an FK to that through model, deletion is cascaded
        from one of the participants in the M2M, to the through model, to its
        related model.
        """
        juan = Child.objects.create(name="Juan")
        paints = Toy.objects.create(name="Paints")
        played = PlayedWith.objects.create(
            child=juan, toy=paints, date=datetime.date.today()
        )
        PlayedWithNote.objects.create(played=played, note="the next Jackson Pollock")
        self.assertEqual(PlayedWithNote.objects.count(), 1)
        paints.delete()
        self.assertEqual(PlayedWith.objects.count(), 0)
        # first two asserts just sanity checks, this is the kicker:
        self.assertEqual(PlayedWithNote.objects.count(), 0)