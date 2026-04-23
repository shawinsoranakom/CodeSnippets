def test_m2m_name_conflict(self):
        # Regression for #11256 - providing an aggregate name
        # that conflicts with an m2m name on the model raises ValueError
        msg = "The annotation 'friends' conflicts with a field on the model."
        with self.assertRaisesMessage(ValueError, msg):
            Author.objects.annotate(friends=Count("friends"))