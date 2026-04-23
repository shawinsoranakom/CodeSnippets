def test_breakpoints(self):
        """Test setting and hitting breakpoints."""
        self._create_script()
        process, client_file = self._connect_and_get_client_file()
        with kill_on_error(process):
            # Skip initial messages until we get to the prompt
            self._read_until_prompt(client_file)

            # Set a breakpoint at the return statement
            self._send_command(client_file, "break bar")
            messages = self._read_until_prompt(client_file)
            bp_msg = next(msg['message'] for msg in messages if 'message' in msg)
            self.assertIn("Breakpoint", bp_msg)

            # Continue execution until breakpoint
            self._send_command(client_file, "c")
            messages = self._read_until_prompt(client_file)

            # Verify we hit the breakpoint
            hit_msg = next(msg['message'] for msg in messages if 'message' in msg)
            self.assertIn("bar()", hit_msg)

            # Check breakpoint list
            self._send_command(client_file, "b")
            messages = self._read_until_prompt(client_file)
            list_msg = next(msg['message'] for msg in reversed(messages) if 'message' in msg)
            self.assertIn("1   breakpoint", list_msg)
            self.assertIn("breakpoint already hit 1 time", list_msg)

            # Clear breakpoint
            self._send_command(client_file, "clear 1")
            messages = self._read_until_prompt(client_file)
            clear_msg = next(msg['message'] for msg in reversed(messages) if 'message' in msg)
            self.assertIn("Deleted breakpoint", clear_msg)

            # Continue to end
            self._send_command(client_file, "c")
            stdout, _ = process.communicate(timeout=SHORT_TIMEOUT)

            self.assertIn("Function returned: 42", stdout)
            self.assertEqual(process.returncode, 0)