def test_hidden_fk_to_m2m(self):
        self.test_fk_to_m2m(related_name="+")