def test_explode(self):
        """An unknown command raises CommandError"""
        with self.assertRaisesMessage(CommandError, "Unknown command: 'explode'"):
            management.call_command(("explode",))