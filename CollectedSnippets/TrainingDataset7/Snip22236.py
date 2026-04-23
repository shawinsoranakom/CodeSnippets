def test_pretty_print_xml_empty_strings(self):
        """
        Regression test for ticket #4558 -- pretty printing of XML fixtures
        doesn't affect parsing of None values.
        """
        # Load a pretty-printed XML fixture with Nulls.
        management.call_command(
            "loaddata",
            "pretty.xml",
            verbosity=0,
        )
        self.assertEqual(Stuff.objects.all()[0].name, "")
        self.assertIsNone(Stuff.objects.all()[0].owner)