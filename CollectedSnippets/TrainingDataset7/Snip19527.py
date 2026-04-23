def test_list_deployment_check_omitted(self):
        call_command("check", list_tags=True)
        self.assertEqual("simpletag\n", sys.stdout.getvalue())