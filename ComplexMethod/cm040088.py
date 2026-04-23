def compute_output_shape(self, sequences_shape, initial_state_shape=None):
        batch_size = sequences_shape[0]
        length = sequences_shape[1]
        states_shape = []
        for state_size in self.state_size:
            if isinstance(state_size, int):
                states_shape.append((batch_size, state_size))
            elif isinstance(state_size, (list, tuple)):
                states_shape.append([(batch_size, s) for s in state_size])

        output_size = getattr(self.cell, "output_size", None)
        if output_size is None:
            output_size = self.state_size[0]
        if not isinstance(output_size, int):
            raise ValueError("output_size must be an integer.")
        if self.return_sequences:
            output_shape = (batch_size, length, output_size)
        else:
            output_shape = (batch_size, output_size)
        if self.return_state:
            return output_shape, *states_shape
        return output_shape