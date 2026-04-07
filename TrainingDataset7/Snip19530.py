def test_tags_deployment_check_included(self):
        call_command("check", deploy=True, tags=["deploymenttag"])
        self.assertIn("Deployment Check", sys.stderr.getvalue())