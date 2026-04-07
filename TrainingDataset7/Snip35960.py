def test_subparser_invalid_option(self):
        msg = r"invalid choice: 'test' \(choose from '?foo'?\)"
        with self.assertRaisesRegex(CommandError, msg):
            management.call_command("subparser", "test", 12)
        msg = "Error: the following arguments are required: subcommand"
        with self.assertRaisesMessage(CommandError, msg):
            management.call_command("subparser_dest", subcommand="foo", bar=12)