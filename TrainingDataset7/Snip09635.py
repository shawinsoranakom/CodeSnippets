def _guess_input_sizes(self, params_list):
        # Try dict handling; if that fails, treat as sequence
        if hasattr(params_list[0], "keys"):
            sizes = {}
            for params in params_list:
                for k, value in params.items():
                    if value.input_size:
                        sizes[k] = value.input_size
            if sizes:
                self.setinputsizes(**sizes)
        else:
            # It's not a list of dicts; it's a list of sequences
            sizes = [None] * len(params_list[0])
            for params in params_list:
                for i, value in enumerate(params):
                    if value.input_size:
                        sizes[i] = value.input_size
            if sizes:
                self.setinputsizes(*sizes)