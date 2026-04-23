def call(self, inputs):
        if not isinstance(inputs, (list, tuple)):
            raise ValueError(
                "A merge layer should be called on a list of inputs. "
                f"Received: inputs={inputs} (not a list of tensors)"
            )
        if self._reshape_required:
            reshaped_inputs = []
            input_ndims = list(map(ops.ndim, inputs))
            if None not in input_ndims:
                # If ranks of all inputs are available,
                # we simply expand each of them at axis=1
                # until all of them have the same rank.
                max_ndim = max(input_ndims)
                for x in inputs:
                    x_ndim = ops.ndim(x)
                    for _ in range(max_ndim - x_ndim):
                        x = ops.expand_dims(x, axis=1)
                    reshaped_inputs.append(x)
                return self._merge_function(reshaped_inputs)
            else:
                # Transpose all inputs so that batch size is the last dimension.
                # (batch_size, dim1, dim2, ... ) -> (dim1, dim2, ... ,
                # batch_size)
                transposed = False
                for x in inputs:
                    x_ndim = ops.ndim(x)

                    if x_ndim is None:
                        x_shape = ops.shape(x)
                        batch_size = x_shape[0]

                        new_shape = backend.concatenate(
                            [x_shape[1:], ops.expand_dims(batch_size, axis=-1)]
                        )
                        x_transposed = ops.reshape(
                            x,
                            ops.stack(
                                [batch_size, ops.prod(x_shape[1:])],
                                axis=0,
                            ),
                        )
                        x_transposed = ops.transpose(x_transposed, perm=(1, 0))
                        x_transposed = ops.reshape(x_transposed, new_shape)

                        reshaped_inputs.append(x_transposed)
                        transposed = True

                    elif x_ndim > 1:
                        dims = list(range(1, x_ndim)) + [0]
                        reshaped_inputs.append(ops.transpose(x, perm=dims))
                        print(dims)
                        transposed = True
                    else:
                        # We don't transpose inputs if they are 1D vectors or
                        # scalars.
                        reshaped_inputs.append(x)

                y = self._merge_function(reshaped_inputs)
                y_ndim = ops.ndim(y)

                if transposed:
                    # If inputs have been transposed, we have to transpose the
                    # output too.
                    if y_ndim is None:
                        y_shape = ops.shape(y)
                        y_ndim = ops.shape(y_shape)[0]
                        batch_size = y_shape[y_ndim - 1]
                        new_shape = ops.concatenate(
                            [
                                ops.expand_dims(batch_size, axis=-1),
                                y_shape[: y_ndim - 1],
                            ]
                        )
                        y = ops.reshape(y, (-1, batch_size))
                        y = ops.transpose(y, perm=(1, 0))
                        y = ops.reshape(y, new_shape)
                    elif y_ndim > 1:
                        dims = [y_ndim - 1] + list(range(y_ndim - 1))
                        y = ops.transpose(y, perm=dims)
                return y
        else:
            return self._merge_function(inputs)