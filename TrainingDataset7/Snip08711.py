def _reordered_actions(self, actions):
        return sorted(
            actions, key=lambda a: set(a.option_strings) & self.show_last != set()
        )