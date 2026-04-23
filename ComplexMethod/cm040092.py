def call(self, sequence, states, training=False):
        prev_output = states[0] if isinstance(states, (list, tuple)) else states
        dp_mask = self.get_dropout_mask(sequence)
        rec_dp_mask = self.get_recurrent_dropout_mask(prev_output)

        if training and dp_mask is not None:
            sequence = sequence * dp_mask
        h = ops.matmul(sequence, self.kernel)
        if self.bias is not None:
            h = ops.add(h, self.bias)

        if training and rec_dp_mask is not None:
            prev_output = prev_output * rec_dp_mask
        output = h + ops.matmul(prev_output, self.recurrent_kernel)
        if self.activation is not None:
            output = self.activation(output)

        new_state = [output] if isinstance(states, (list, tuple)) else output
        return output, new_state