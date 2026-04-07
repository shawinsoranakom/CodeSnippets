def test_initial_data(self):
        """Test instance independence of initial data dict (see #16138)"""
        initial_1 = FormMixin().get_initial()
        initial_1["foo"] = "bar"
        initial_2 = FormMixin().get_initial()
        self.assertNotEqual(initial_1, initial_2)