def test_list_tags_empty(self):
        call_command("check", list_tags=True)
        self.assertEqual("\n", sys.stdout.getvalue())