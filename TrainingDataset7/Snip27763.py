def test_do_not_call_in_templates_nonmember(self):
        self.assertNotIn("do_not_call_in_templates", Suit.__members__)
        self.assertIs(Suit.do_not_call_in_templates, True)