def test_permlookupdict_in(self):
        """
        No endless loops if accessed with 'in' - refs #18979.
        """
        pldict = PermLookupDict(MockUser(), "mockapp")
        with self.assertRaises(TypeError):
            self.EQLimiterObject() in pldict