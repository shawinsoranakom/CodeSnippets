def compute_output_shape(self, input_shape):
        if self.data_format == "channels_first":
            dim1 = (
                self.size[0] * input_shape[2]
                if input_shape[2] is not None
                else None
            )
            dim2 = (
                self.size[1] * input_shape[3]
                if input_shape[3] is not None
                else None
            )
            dim3 = (
                self.size[2] * input_shape[4]
                if input_shape[4] is not None
                else None
            )
            return (input_shape[0], input_shape[1], dim1, dim2, dim3)
        else:
            dim1 = (
                self.size[0] * input_shape[1]
                if input_shape[1] is not None
                else None
            )
            dim2 = (
                self.size[1] * input_shape[2]
                if input_shape[2] is not None
                else None
            )
            dim3 = (
                self.size[2] * input_shape[3]
                if input_shape[3] is not None
                else None
            )
            return (input_shape[0], dim1, dim2, dim3, input_shape[4])