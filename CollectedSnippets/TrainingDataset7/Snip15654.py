def assertInAfterFormatting(self, member, container, msg=None):
        if HAS_BLACK:
            import black

            # Black does not have a stable API, but this is still less fragile
            # than attempting to filter out all paths where it is available.
            member = black.format_str(member, mode=black.FileMode())

        self.assertIn(member, container, msg=msg)