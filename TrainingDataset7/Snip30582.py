def test_ticket7378(self):
        self.assertSequenceEqual(self.a1.report_set.all(), [self.r1])