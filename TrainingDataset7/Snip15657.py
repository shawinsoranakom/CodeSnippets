def assertNotInOutput(self, stream, msg):
        """
        Utility assertion: assert that the given message doesn't exist in the
        output
        """
        self.assertNotIn(
            msg, stream, "'%s' matches actual output text '%s'" % (msg, stream)
        )