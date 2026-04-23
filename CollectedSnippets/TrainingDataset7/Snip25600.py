def test_hidden_fk_to_fk(self):
        self.test_fk_to_fk(related_name="+")