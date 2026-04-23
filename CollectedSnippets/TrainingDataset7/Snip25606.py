def test_hidden_m2m_to_fk(self):
        self.test_m2m_to_fk(related_name="+")