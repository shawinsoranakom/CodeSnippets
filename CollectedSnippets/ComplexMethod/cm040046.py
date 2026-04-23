def _flip_inputs(self, inputs, transformation):
        if transformation is None:
            return inputs

        flips = transformation["flips"]
        inputs_shape = self.backend.shape(inputs)
        unbatched = len(inputs_shape) == 3
        if unbatched:
            inputs = self.backend.numpy.expand_dims(inputs, axis=0)

        flipped_outputs = inputs
        if self.data_format == "channels_last":
            horizontal_axis = -2
            vertical_axis = -3
        else:
            horizontal_axis = -1
            vertical_axis = -2

        if self.mode == HORIZONTAL or self.mode == HORIZONTAL_AND_VERTICAL:
            flipped_outputs = self.backend.numpy.where(
                flips,
                self.backend.numpy.flip(flipped_outputs, axis=horizontal_axis),
                flipped_outputs,
            )
        if self.mode == VERTICAL or self.mode == HORIZONTAL_AND_VERTICAL:
            flipped_outputs = self.backend.numpy.where(
                flips,
                self.backend.numpy.flip(flipped_outputs, axis=vertical_axis),
                flipped_outputs,
            )
        if unbatched:
            flipped_outputs = self.backend.numpy.squeeze(
                flipped_outputs, axis=0
            )
        return flipped_outputs