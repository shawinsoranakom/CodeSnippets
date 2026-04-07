def slice_expression(self, expression, start, length):
        # If length is not provided, don't specify an end to slice to the end
        # of the array.
        end = None if length is None else start + length - 1
        return SliceTransform(start, end, expression)