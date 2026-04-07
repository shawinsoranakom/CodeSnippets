def get_with_params(self):
        with_params = []
        if self.buffering is not None:
            with_params.append("buffering = %s" % ("on" if self.buffering else "off"))
        if self.fillfactor is not None:
            with_params.append("fillfactor = %d" % self.fillfactor)
        return with_params