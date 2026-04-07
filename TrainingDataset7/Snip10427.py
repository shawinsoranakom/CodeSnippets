def ask_merge(self, app_label):
        return self._boolean_input(
            "\nMerging will only work if the operations printed above do not conflict\n"
            + "with each other (working on different fields or models)\n"
            + "Should these migration branches be merged? [y/N]",
            False,
        )