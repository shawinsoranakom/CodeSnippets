def test_get_or_create_integrityerror(self):
        """
        Regression test for #15117. Requires a TransactionTestCase on
        databases that delay integrity checks until the end of transactions,
        otherwise the exception is never raised.
        """
        try:
            Profile.objects.get_or_create(person=Person(id=1))
        except IntegrityError:
            pass
        else:
            self.skipTest("This backend does not support integrity checks.")