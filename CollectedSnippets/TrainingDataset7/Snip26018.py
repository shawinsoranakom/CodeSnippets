def test_m2m_query(self):
        result = self.event.teams.all()
        self.assertCountEqual(result, [self.team_alpha])