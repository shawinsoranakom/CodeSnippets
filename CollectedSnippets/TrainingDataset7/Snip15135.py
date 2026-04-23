def test_distinct_for_m2m_to_inherited_in_list_filter(self):
        """
        Regression test for #13902: When using a ManyToMany in list_filter,
        results shouldn't appear more than once. Target of the relationship
        inherits from another.
        """
        lead = ChordsMusician.objects.create(name="Player A")
        three = ChordsBand.objects.create(name="The Chords Trio")
        Invitation.objects.create(band=three, player=lead, instrument="guitar")
        Invitation.objects.create(band=three, player=lead, instrument="bass")

        m = ChordsBandAdmin(ChordsBand, custom_site)
        request = self.factory.get("/chordsband/", data={"members": lead.pk})
        request.user = self.superuser

        cl = m.get_changelist_instance(request)
        cl.get_results(request)

        # There's only one ChordsBand instance
        self.assertEqual(cl.result_count, 1)