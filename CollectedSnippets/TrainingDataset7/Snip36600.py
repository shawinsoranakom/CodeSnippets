def __format__(self, specifier, **kwargs):
                amount = super().__format__(specifier, **kwargs)
                return "€ {}".format(amount)