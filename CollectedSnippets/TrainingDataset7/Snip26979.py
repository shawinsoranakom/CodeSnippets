def test(from_state, to_state, msg):
            changes = self.get_changes([from_state], [to_state])
            if changes:
                ops = ", ".join(
                    o.__class__.__name__ for o in changes["a"][0].operations
                )
                self.fail("Created operation(s) %s from %s" % (ops, msg))