def test_select_related(self):
        """
        Boolean fields retrieved via select_related() should return booleans.
        """
        bmt = BooleanModel.objects.create(bfield=True)
        bmf = BooleanModel.objects.create(bfield=False)
        nbmt = NullBooleanModel.objects.create(nbfield=True)
        nbmf = NullBooleanModel.objects.create(nbfield=False)
        m1 = FksToBooleans.objects.create(bf=bmt, nbf=nbmt)
        m2 = FksToBooleans.objects.create(bf=bmf, nbf=nbmf)

        # select_related('fk_field_name')
        ma = FksToBooleans.objects.select_related("bf").get(pk=m1.id)
        self.assertIs(ma.bf.bfield, True)
        self.assertIs(ma.nbf.nbfield, True)

        # select_related()
        mb = FksToBooleans.objects.select_related().get(pk=m1.id)
        mc = FksToBooleans.objects.select_related().get(pk=m2.id)
        self.assertIs(mb.bf.bfield, True)
        self.assertIs(mb.nbf.nbfield, True)
        self.assertIs(mc.bf.bfield, False)
        self.assertIs(mc.nbf.nbfield, False)