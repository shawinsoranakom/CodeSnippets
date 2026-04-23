def get_with_params(self):
        with_params = []
        if self.gin_pending_list_limit is not None:
            with_params.append(
                "gin_pending_list_limit = %d" % self.gin_pending_list_limit
            )
        if self.fastupdate is not None:
            with_params.append("fastupdate = %s" % ("on" if self.fastupdate else "off"))
        return with_params