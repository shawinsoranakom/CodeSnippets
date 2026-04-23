def test_correct_type_proxy_of_proxy(self):
        """
        Correct type when querying a proxy of proxy
        """
        Person.objects.create(name="Foo McBar")
        MyPerson.objects.create(name="Bazza del Frob")
        LowerStatusPerson.objects.create(status="low", name="homer")
        pp = sorted(mpp.name for mpp in MyPersonProxy.objects.all())
        self.assertEqual(pp, ["Bazza del Frob", "Foo McBar", "homer"])