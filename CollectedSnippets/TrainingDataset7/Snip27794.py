def test_return_type(self):
        b = BooleanModel.objects.create(bfield=True)
        b.refresh_from_db()
        self.assertIs(b.bfield, True)

        b2 = BooleanModel.objects.create(bfield=False)
        b2.refresh_from_db()
        self.assertIs(b2.bfield, False)

        b3 = NullBooleanModel.objects.create(nbfield=True)
        b3.refresh_from_db()
        self.assertIs(b3.nbfield, True)

        b4 = NullBooleanModel.objects.create(nbfield=False)
        b4.refresh_from_db()
        self.assertIs(b4.nbfield, False)