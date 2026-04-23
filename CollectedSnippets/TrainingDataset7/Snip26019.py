def test_m2m_reverse_query(self):
        result = self.chris.event_set.all()
        self.assertCountEqual(result, [self.event])