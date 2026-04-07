def test_list_deployment_check_included(self):
        call_command("check", deploy=True, list_tags=True)
        self.assertEqual("deploymenttag\nsimpletag\n", sys.stdout.getvalue())