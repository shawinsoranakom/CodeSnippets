def test_ticket_21879(self):
        cpt1 = CustomPkTag.objects.create(id="cpt1", tag="cpt1")
        cp1 = CustomPk.objects.create(name="cp1", extra="extra")
        cp1.custompktag_set.add(cpt1)
        self.assertSequenceEqual(CustomPk.objects.filter(custompktag=cpt1), [cp1])
        self.assertSequenceEqual(CustomPkTag.objects.filter(custom_pk=cp1), [cpt1])