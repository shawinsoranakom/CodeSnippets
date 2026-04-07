def test_m2m_reverse_query_proxied(self):
        result = self.chris.special_event_set.all()
        self.assertCountEqual(result, [self.event])