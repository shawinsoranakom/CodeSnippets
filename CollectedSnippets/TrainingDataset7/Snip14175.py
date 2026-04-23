def _get_clock(self, root):
        return self.client.query("clock", root)["clock"]