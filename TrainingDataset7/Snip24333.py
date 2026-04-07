def test_infinite_values_equals_identical(self):
        # Input with identical infinite values are equals_identical.
        g1 = Point(x=float("nan"), y=math.inf)
        g2 = Point(x=float("nan"), y=math.inf)
        self.assertIs(g1.equals_identical(g2), True)