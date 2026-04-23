def build(self, input_shape):
        # Used purely for shape validation.
        if len(input_shape) < 1 or not isinstance(
            input_shape[0], (tuple, list)
        ):
            raise ValueError(
                "A `Concatenate` layer should be called on a list of "
                f"at least 1 input. Received: input_shape={input_shape}"
            )
        if all(shape is None for shape in input_shape):
            return

        reduced_inputs_shapes = [list(shape) for shape in input_shape]
        reduced_inputs_shapes_copy = copy.copy(reduced_inputs_shapes)
        shape_set = set()
        for i in range(len(reduced_inputs_shapes_copy)):
            # Convert self.axis to positive axis for each input
            # in case self.axis is a negative number
            concat_axis = self.axis % len(reduced_inputs_shapes_copy[i])
            #  Skip batch axis.
            for axis, axis_value in enumerate(
                reduced_inputs_shapes_copy, start=1
            ):
                # Remove squeezable axes (axes with value of 1)
                # if not in the axis that will be used for concatenation
                # otherwise leave it.
                # This approach allows building the layer,
                # but if tensor shapes are not the same when
                # calling, an exception will be raised.
                if axis != concat_axis and axis_value == 1:
                    del reduced_inputs_shapes[i][axis]

            if len(reduced_inputs_shapes[i]) > self.axis:
                del reduced_inputs_shapes[i][self.axis]
            shape_set.add(tuple(reduced_inputs_shapes[i]))

        if len(shape_set) != 1:
            err_msg = (
                "A `Concatenate` layer requires inputs with matching shapes "
                "except for the concatenation axis. "
                f"Received: input_shape={input_shape}"
            )
            # Make sure all the shapes have same ranks.
            ranks = set(len(shape) for shape in shape_set)
            if len(ranks) != 1:
                raise ValueError(err_msg)
            # Get the only rank for the set.
            (rank,) = ranks
            for axis in range(rank):
                # Skip the Nones in the shape since they are dynamic, also the
                # axis for concat has been removed above.
                unique_dims = set(
                    shape[axis]
                    for shape in shape_set
                    if shape[axis] is not None
                )
                if len(unique_dims) > 1:
                    raise ValueError(err_msg)