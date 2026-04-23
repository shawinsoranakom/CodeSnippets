def assertDeprecatedIn70(self, params, name):
        return self.assertWarnsMessage(
            RemovedInDjango70Warning,
            f"Passing positional argument(s) {params} to {name}() is deprecated.",
        )