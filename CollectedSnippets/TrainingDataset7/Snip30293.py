def test_basic_proxy_reverse(self):
        """
        A new MyPerson also shows up as a standard Person.
        """
        MyPerson.objects.create(name="Bazza del Frob")
        self.assertEqual(len(MyPerson.objects.all()), 1)
        self.assertEqual(len(Person.objects.all()), 1)

        LowerStatusPerson.objects.create(status="low", name="homer")
        lsps = [lsp.name for lsp in LowerStatusPerson.objects.all()]
        self.assertEqual(lsps, ["homer"])