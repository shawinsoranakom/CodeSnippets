def test_null_default(self):
        """
        A BooleanField defaults to None, which isn't a valid value (#15124).
        """
        boolean_field = BooleanModel._meta.get_field("bfield")
        self.assertFalse(boolean_field.has_default())
        b = BooleanModel()
        self.assertIsNone(b.bfield)
        with transaction.atomic():
            with self.assertRaises(IntegrityError):
                b.save()

        nb = NullBooleanModel()
        self.assertIsNone(nb.nbfield)
        nb.save()