def test_do_not_call_in_templates_member(self):
        # do_not_call_in_templates is not implicitly treated as a member.
        Special = models.IntegerChoices("Special", "do_not_call_in_templates")
        self.assertIn("do_not_call_in_templates", Special.__members__)
        self.assertEqual(
            Special.do_not_call_in_templates.label,
            "Do Not Call In Templates",
        )
        self.assertEqual(Special.do_not_call_in_templates.value, 1)
        self.assertEqual(
            Special.do_not_call_in_templates.name,
            "do_not_call_in_templates",
        )