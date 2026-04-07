def assertDeprecated(self, params, name):
        msg = (
            "Passing positional argument(s) {0} to {1}() is deprecated. Use keyword "
            "arguments instead."
        )
        return self.assertWarnsMessage(
            RemovedAfterNextVersionWarning, msg.format(params, name)
        )