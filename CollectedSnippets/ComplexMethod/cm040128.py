def _compute_elemwise_op_output_shape(self, shape1, shape2):
        """Computes the shape of the resultant of an elementwise operation.

        Args:
            shape1: Tuple or None. Shape of the first tensor
            shape2: Tuple or None. Shape of the second tensor

        Returns:
            Expected output shape when an element-wise operation is
            carried out on 2 tensors with shapes shape1 and shape2.
            tuple or None.

        Raises:
            ValueError: If shape1 and shape2 are not compatible for
                element-wise operations.
        """

        if None in [shape1, shape2]:
            return None
        elif len(shape1) < len(shape2):
            return self._compute_elemwise_op_output_shape(shape2, shape1)
        elif not shape2:
            return shape1
        output_shape = list(shape1[: -len(shape2)])
        for i, j in zip(shape1[-len(shape2) :], shape2):
            if i is None or j is None:
                output_shape.append(None)
            elif i == 1:
                output_shape.append(j)
            elif j == 1:
                output_shape.append(i)
            else:
                if i != j:
                    raise ValueError(
                        "Inputs have incompatible shapes. "
                        f"Received shapes {shape1} and {shape2}"
                    )
                output_shape.append(i)
        return tuple(output_shape)