def test_reverse_relation_name_conflict(self):
        # Regression for #11256 - providing an aggregate name
        # that conflicts with a reverse-related name on the model raises
        # ValueError
        msg = "The annotation 'book_contact_set' conflicts with a field on the model."
        with self.assertRaisesMessage(ValueError, msg):
            Author.objects.annotate(book_contact_set=Avg("friends__age"))