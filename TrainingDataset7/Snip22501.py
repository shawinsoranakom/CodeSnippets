def test_choicefield_mapping(self):
        f = ChoiceField(choices={"J": "John", "P": "Paul"})
        self.assertEqual("J", f.clean("J"))