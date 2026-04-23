def build(self, input_shape):
        # Used purely for shape validation.
        if (
            not isinstance(input_shape[0], (tuple, list))
            or len(input_shape) != 2
        ):
            raise ValueError(
                f"A `Dot` layer should be called on a list of 2 inputs. "
                f"Received: input_shape={input_shape}"
            )
        shape1 = input_shape[0]
        shape2 = input_shape[1]
        if shape1 is None or shape2 is None:
            return
        if isinstance(self.axes, int):
            if self.axes < 0:
                axes = [self.axes % len(shape1), self.axes % len(shape2)]
            else:
                axes = [self.axes] * 2
        else:
            axes = self.axes
        if shape1[axes[0]] != shape2[axes[1]]:
            raise ValueError(
                f"Incompatible input shapes: "
                f"axis values {shape1[axes[0]]} (at axis {axes[0]}) != "
                f"{shape2[axes[1]]} (at axis {axes[1]}). "
                f"Full input shapes: {shape1}, {shape2}"
            )