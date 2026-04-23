def test_no_existent_external_program(self):
        msg = "Error executing a_42_command_that_doesnt_exist_42"
        with self.assertRaisesMessage(CommandError, msg):
            popen_wrapper(["a_42_command_that_doesnt_exist_42"])