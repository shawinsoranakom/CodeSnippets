def test_fk_attname_conflict(self):
        msg = "The annotation 'contact_id' conflicts with a field on the model."
        with self.assertRaisesMessage(ValueError, msg):
            Book.objects.annotate(contact_id=F("publisher_id"))