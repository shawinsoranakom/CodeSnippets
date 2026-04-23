def _request_component(self, path):
        return self.fetch("/component/%s" % path, method="GET")