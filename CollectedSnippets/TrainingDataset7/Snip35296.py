def __call__(self, result=None):
        # Detect fixture loading by counting SQL queries, should be zero
        with self.assertNumQueries(0):
            super().__call__(result)