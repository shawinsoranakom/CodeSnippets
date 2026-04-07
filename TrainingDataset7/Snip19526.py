def test_list_tags(self):
        call_command("check", list_tags=True)
        self.assertEqual("simpletag\n", sys.stdout.getvalue())