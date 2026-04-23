def call(self, inputs, states, training=False):
        h_tm1 = states[0]  # previous memory state
        c_tm1 = states[1]  # previous carry state

        if self.implementation == 1:
            if training and 0.0 < self.dropout < 1.0:
                dp_mask = self.get_dropout_mask(inputs)
                inputs_i = inputs * dp_mask[0]
                inputs_f = inputs * dp_mask[1]
                inputs_c = inputs * dp_mask[2]
                inputs_o = inputs * dp_mask[3]
            else:
                inputs_i = inputs
                inputs_f = inputs
                inputs_c = inputs
                inputs_o = inputs
            k_i, k_f, k_c, k_o = ops.split(self.kernel, 4, axis=1)
            x_i = ops.matmul(inputs_i, k_i)
            x_f = ops.matmul(inputs_f, k_f)
            x_c = ops.matmul(inputs_c, k_c)
            x_o = ops.matmul(inputs_o, k_o)
            if self.use_bias:
                b_i, b_f, b_c, b_o = ops.split(self.bias, 4, axis=0)
                x_i += b_i
                x_f += b_f
                x_c += b_c
                x_o += b_o

            if training and 0.0 < self.recurrent_dropout < 1.0:
                rec_dp_mask = self.get_recurrent_dropout_mask(h_tm1)
                h_tm1_i = h_tm1 * rec_dp_mask[0]
                h_tm1_f = h_tm1 * rec_dp_mask[1]
                h_tm1_c = h_tm1 * rec_dp_mask[2]
                h_tm1_o = h_tm1 * rec_dp_mask[3]
            else:
                h_tm1_i = h_tm1
                h_tm1_f = h_tm1
                h_tm1_c = h_tm1
                h_tm1_o = h_tm1
            x = (x_i, x_f, x_c, x_o)
            h_tm1 = (h_tm1_i, h_tm1_f, h_tm1_c, h_tm1_o)
            c, o = self._compute_carry_and_output(x, h_tm1, c_tm1)
        else:
            if training and 0.0 < self.dropout < 1.0:
                dp_mask = self.get_dropout_mask(inputs)
                inputs = inputs * dp_mask

            z = ops.matmul(inputs, self.kernel)

            z = ops.add(z, ops.matmul(h_tm1, self.recurrent_kernel))
            if self.use_bias:
                z = ops.add(z, self.bias)

            z = ops.split(z, 4, axis=1)
            c, o = self._compute_carry_and_output_fused(z, c_tm1)

        h = o * self.activation(c)
        return h, [h, c]