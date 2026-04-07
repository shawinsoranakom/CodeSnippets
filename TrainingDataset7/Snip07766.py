def get_with_params(self):
        with_params = []
        if self.length is not None:
            with_params.append("length = %d" % self.length)
        if self.columns:
            with_params.extend(
                "col%d = %d" % (i, v) for i, v in enumerate(self.columns, start=1)
            )
        return with_params