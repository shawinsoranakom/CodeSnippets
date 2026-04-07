def test_field_name_conflict(self):
        # Regression for #11256 - providing an aggregate name
        # that conflicts with a field name on the model raises ValueError
        msg = "The annotation 'age' conflicts with a field on the model."
        with self.assertRaisesMessage(ValueError, msg):
            Author.objects.annotate(age=Avg("friends__age"))