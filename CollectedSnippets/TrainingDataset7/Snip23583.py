def test_q_object_or(self):
        """
        SQL query parameters for generic relations are properly
        grouped when OR is used (#11535).

        In this bug the first query (below) works while the second, with the
        query parameters the same but in reverse order, does not.

        The issue is that the generic relation conditions do not get properly
        grouped in parentheses.
        """
        note_contact = Contact.objects.create()
        org_contact = Contact.objects.create()
        Note.objects.create(note="note", content_object=note_contact)
        org = Organization.objects.create(name="org name")
        org.contacts.add(org_contact)
        # search with a non-matching note and a matching org name
        qs = Contact.objects.filter(
            Q(notes__note__icontains=r"other note")
            | Q(organizations__name__icontains=r"org name")
        )
        self.assertIn(org_contact, qs)
        # search again, with the same query parameters, in reverse order
        qs = Contact.objects.filter(
            Q(organizations__name__icontains=r"org name")
            | Q(notes__note__icontains=r"other note")
        )
        self.assertIn(org_contact, qs)