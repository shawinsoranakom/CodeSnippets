def test_foreign_key_delete_nullifies_correct_columns(self):
        """
        With a model (Researcher) that has two foreign keys pointing to the
        same model (Contact), deleting an instance of the target model
        (contact1) nullifies the correct fields of Researcher.
        """
        contact1 = Contact.objects.create(label="Contact 1")
        contact2 = Contact.objects.create(label="Contact 2")
        researcher1 = Researcher.objects.create(
            primary_contact=contact1,
            secondary_contact=contact2,
        )
        researcher2 = Researcher.objects.create(
            primary_contact=contact2,
            secondary_contact=contact1,
        )
        contact1.delete()
        researcher1.refresh_from_db()
        researcher2.refresh_from_db()
        self.assertIsNone(researcher1.primary_contact)
        self.assertEqual(researcher1.secondary_contact, contact2)
        self.assertEqual(researcher2.primary_contact, contact2)
        self.assertIsNone(researcher2.secondary_contact)