def test_logic(sess, initial):
            self.assertIn("Entering Dynamo-generated code: fn", initial)
            # Step into the resume function
            output = initial
            while (
                "Entering Dynamo-generated code: " + TORCH_DYNAMO_RESUME_IN_PREFIX
                not in output
            ):
                output = yield "s"

            # bt should show both frames, with the resume function selected
            bt_output = yield "bt"
            lines = [l.strip() for l in bt_output.split("\n") if "[" in l and "]" in l]
            self.assertEqual(len(lines), 2)
            # First frame is fn (no > marker since we're viewing the callee)
            self.assertIn("fn", lines[0])
            self.assertNotIn(">", lines[0])
            # Second frame is resume function (> marker since it's current)
            self.assertIn(">", lines[1])
            self.assertIn(TORCH_DYNAMO_RESUME_IN_PREFIX, lines[1])

            # Move up and bt again — marker should move to fn
            yield "u"
            bt_output = yield "bt"
            lines = [l.strip() for l in bt_output.split("\n") if "[" in l and "]" in l]
            self.assertIn(">", lines[0])
            self.assertNotIn(">", lines[1])

            # Continue to end
            yield "c"