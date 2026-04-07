def ask_merge(self, app_label):
        """Should these migrations really be merged?"""
        return self.defaults.get("ask_merge", False)