def wasSuccessful(self):
        """Tells whether or not this result was a success."""
        failure_types = {"addError", "addFailure", "addSubTest", "addUnexpectedSuccess"}
        return all(e[0] not in failure_types for e in self.events)