def call(self, inputs, states, training=False):
        h_tm1 = (
            states[0] if tree.is_nested(states) else states
        )  # previous state

        if self.use_bias:
            if not self.reset_after:
                input_bias, recurrent_bias = self.bias, None
            else:
                input_bias, recurrent_bias = (
                    ops.squeeze(e, axis=0)
                    for e in ops.split(self.bias, self.bias.shape[0], axis=0)
                )

        if self.implementation == 1:
            if training and 0.0 < self.dropout < 1.0:
                dp_mask = self.get_dropout_mask(inputs)
                inputs_z = inputs * dp_mask[0]
                inputs_r = inputs * dp_mask[1]
                inputs_h = inputs * dp_mask[2]
            else:
                inputs_z = inputs
                inputs_r = inputs
                inputs_h = inputs

            x_z = ops.matmul(inputs_z, self.kernel[:, : self.units])
            x_r = ops.matmul(
                inputs_r, self.kernel[:, self.units : self.units * 2]
            )
            x_h = ops.matmul(inputs_h, self.kernel[:, self.units * 2 :])

            if self.use_bias:
                x_z += input_bias[: self.units]
                x_r += input_bias[self.units : self.units * 2]
                x_h += input_bias[self.units * 2 :]

            if training and 0.0 < self.recurrent_dropout < 1.0:
                rec_dp_mask = self.get_recurrent_dropout_mask(h_tm1)
                h_tm1_z = h_tm1 * rec_dp_mask[0]
                h_tm1_r = h_tm1 * rec_dp_mask[1]
                h_tm1_h = h_tm1 * rec_dp_mask[2]
            else:
                h_tm1_z = h_tm1
                h_tm1_r = h_tm1
                h_tm1_h = h_tm1

            recurrent_z = ops.matmul(
                h_tm1_z, self.recurrent_kernel[:, : self.units]
            )
            recurrent_r = ops.matmul(
                h_tm1_r, self.recurrent_kernel[:, self.units : self.units * 2]
            )
            if self.reset_after and self.use_bias:
                recurrent_z += recurrent_bias[: self.units]
                recurrent_r += recurrent_bias[self.units : self.units * 2]

            z = self.recurrent_activation(x_z + recurrent_z)
            r = self.recurrent_activation(x_r + recurrent_r)

            # reset gate applied after/before matrix multiplication
            if self.reset_after:
                recurrent_h = ops.matmul(
                    h_tm1_h, self.recurrent_kernel[:, self.units * 2 :]
                )
                if self.use_bias:
                    recurrent_h += recurrent_bias[self.units * 2 :]
                recurrent_h = r * recurrent_h
            else:
                recurrent_h = ops.matmul(
                    r * h_tm1_h, self.recurrent_kernel[:, self.units * 2 :]
                )

            hh = self.activation(x_h + recurrent_h)
        else:
            if training and 0.0 < self.dropout < 1.0:
                dp_mask = self.get_dropout_mask(inputs)
                inputs = inputs * dp_mask

            # inputs projected by all gate matrices at once
            matrix_x = ops.matmul(inputs, self.kernel)
            if self.use_bias:
                # biases: bias_z_i, bias_r_i, bias_h_i
                matrix_x = ops.add(matrix_x, input_bias)

            x_z, x_r, x_h = ops.split(matrix_x, 3, axis=-1)

            if self.reset_after:
                # hidden state projected by all gate matrices at once
                matrix_inner = ops.matmul(h_tm1, self.recurrent_kernel)
                if self.use_bias:
                    matrix_inner += recurrent_bias
            else:
                # hidden state projected separately for update/reset and new
                matrix_inner = ops.matmul(
                    h_tm1, self.recurrent_kernel[:, : 2 * self.units]
                )

            recurrent_z = matrix_inner[:, : self.units]
            recurrent_r = matrix_inner[:, self.units : self.units * 2]
            recurrent_h = matrix_inner[:, self.units * 2 :]

            z = self.recurrent_activation(x_z + recurrent_z)
            r = self.recurrent_activation(x_r + recurrent_r)

            if self.reset_after:
                recurrent_h = r * recurrent_h
            else:
                recurrent_h = ops.matmul(
                    r * h_tm1, self.recurrent_kernel[:, 2 * self.units :]
                )

            hh = self.activation(x_h + recurrent_h)

        # previous and candidate state mixed by update gate
        h = z * h_tm1 + (1 - z) * hh
        new_state = [h] if tree.is_nested(states) else h
        return h, new_state