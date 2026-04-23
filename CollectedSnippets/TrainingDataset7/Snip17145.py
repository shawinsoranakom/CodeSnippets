def test_fobj_group_by(self):
        """
        An F() object referring to related column works correctly in group by.
        """
        qs = Book.objects.annotate(account=Count("authors")).filter(
            account=F("publisher__num_awards")
        )
        self.assertQuerySetEqual(
            qs, ["Sams Teach Yourself Django in 24 Hours"], lambda b: b.name
        )