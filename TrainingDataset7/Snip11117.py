def context(self):
        return decimal.Context(prec=self.max_digits)