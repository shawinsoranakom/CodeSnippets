def _expand_for_data_format(values):
        """
        Convert values to be in the format expected by np.pad based on the data format.
        """
        if isinstance(values, (int, float)):
            values = ((values, values), (values, values))
        elif isinstance(values, tuple) and len(values) == 1:
            values = ((values[0], values[0]), (values[0], values[0]))
        elif isinstance(values, tuple) and len(values) == 2 and isinstance(values[0], int):
            values = (values, values)
        elif isinstance(values, tuple) and len(values) == 2 and isinstance(values[0], tuple):
            pass
        else:
            raise ValueError(f"Unsupported format: {values}")

        # add 0 for channel dimension
        values = ((0, 0), *values) if input_data_format == ChannelDimension.FIRST else (*values, (0, 0))

        # Add additional padding if there's a batch dimension
        values = ((0, 0), *values) if image.ndim == 4 else values
        return values