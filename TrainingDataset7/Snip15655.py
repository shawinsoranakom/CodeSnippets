def assertNoOutput(self, stream):
        "Utility assertion: assert that the given stream is empty"
        self.assertEqual(
            len(stream), 0, "Stream should be empty: actually contains '%s'" % stream
        )