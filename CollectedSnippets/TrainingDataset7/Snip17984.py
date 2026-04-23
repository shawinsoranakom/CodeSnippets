def test_keyboard_interrupt(self):
        new_io = StringIO()
        with self.assertRaises(SystemExit):
            call_command(
                "createsuperuser",
                interactive=True,
                stdin=MockTTY(),
                stdout=new_io,
                stderr=new_io,
            )
        self.assertEqual(new_io.getvalue(), "\nOperation cancelled.\n")