def test_safestr(self):
        c = Company(cents_paid=12, products_delivered=1)
        c.name = SafeString("Iñtërnâtiônàlizætiøn1")
        c.save()