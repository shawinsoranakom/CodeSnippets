def test_chained_fks(self):
        """
        Chained foreign keys with to_field produce incorrect query.
        """

        m1 = Model1.objects.create(pkey=1000)
        m2 = Model2.objects.create(model1=m1)
        m3 = Model3.objects.create(model2=m2)

        # this is the actual test for #18432
        m3 = Model3.objects.get(model2=1000)
        m3.model2