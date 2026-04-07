def get_with_params(self):
        with_params = []
        if self.autosummarize is not None:
            with_params.append(
                "autosummarize = %s" % ("on" if self.autosummarize else "off")
            )
        if self.pages_per_range is not None:
            with_params.append("pages_per_range = %d" % self.pages_per_range)
        return with_params