def test_decimal_subclass(self):
        class EuroDecimal(Decimal):
            """
            Wrapper for Decimal which prefixes each amount with the € symbol.
            """

            def __format__(self, specifier, **kwargs):
                amount = super().__format__(specifier, **kwargs)
                return "€ {}".format(amount)

        price = EuroDecimal("1.23")
        self.assertEqual(nformat(price, ","), "€ 1,23")