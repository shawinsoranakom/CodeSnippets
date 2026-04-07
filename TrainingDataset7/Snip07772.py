def get_with_params(self):
        with_params = []
        if self.fillfactor is not None:
            with_params.append("fillfactor = %d" % self.fillfactor)
        if self.deduplicate_items is not None:
            with_params.append(
                "deduplicate_items = %s" % ("on" if self.deduplicate_items else "off")
            )
        return with_params