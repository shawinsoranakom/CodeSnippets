def call(self, inputs, states, training=False, **kwargs):
        # Call the cells in order and store the returned states.
        new_states = []
        for cell, states in zip(self.cells, states):
            state_is_list = tree.is_nested(states)
            states = list(states) if tree.is_nested(states) else [states]
            if isinstance(cell, Layer) and cell._call_has_training_arg:
                kwargs["training"] = training
            else:
                kwargs.pop("training", None)
            cell_call_fn = cell.__call__ if callable(cell) else cell.call
            inputs, states = cell_call_fn(inputs, states, **kwargs)
            if len(states) == 1 and not state_is_list:
                states = states[0]
            new_states.append(states)

        if len(new_states) == 1:
            new_states = new_states[0]
        return inputs, new_states