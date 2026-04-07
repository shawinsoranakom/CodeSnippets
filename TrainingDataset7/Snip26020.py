def test_m2m_query_proxied(self):
        result = self.event.special_people.all()
        self.assertCountEqual(result, [self.chris, self.dan])