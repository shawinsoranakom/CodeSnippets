def test(self):
            with self.assertRaisesMessage(CommandError, msg):
                call_command(
                    "createsuperuser",
                    group=nonexistent_group_id,
                    stdin=MockTTY(),
                    verbosity=0,
                )