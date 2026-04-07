def __init__(self, *args, connections_override=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.connections_override = connections_override