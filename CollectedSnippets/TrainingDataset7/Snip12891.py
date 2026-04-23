def _current_scheme_host(self):
        return "{}://{}".format(self.scheme, self.get_host())