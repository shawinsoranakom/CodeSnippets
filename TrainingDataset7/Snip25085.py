def setUp(self):
        super().setUp()
        self.n = decimal.Decimal("66666.666")
        self.f = 99999.999
        self.d = datetime.date(2009, 12, 31)
        self.dt = datetime.datetime(2009, 12, 31, 20, 50)
        self.t = datetime.time(10, 15, 48)
        self.long = 10000
        self.ctxt = Context(
            {
                "n": self.n,
                "t": self.t,
                "d": self.d,
                "dt": self.dt,
                "f": self.f,
                "l": self.long,
            }
        )