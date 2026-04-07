def test_tags_deployment_check_omitted(self):
        msg = 'There is no system check with the "deploymenttag" tag.'
        with self.assertRaisesMessage(CommandError, msg):
            call_command("check", tags=["deploymenttag"])