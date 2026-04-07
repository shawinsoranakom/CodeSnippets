def __init__(self, partial_name, partial_mapping):
        # Defer lookup in `partial_mapping` and nodelist to runtime.
        self.partial_name = partial_name
        self.partial_mapping = partial_mapping