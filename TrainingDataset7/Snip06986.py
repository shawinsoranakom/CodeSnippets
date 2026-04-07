def _topology(self, func, other):
        """A generalized function for topology operations, takes a GDAL
        function and the other geometry to perform the operation on."""
        if not isinstance(other, OGRGeometry):
            raise TypeError(
                "Must use another OGRGeometry object for topology operations!"
            )

        # Returning the output of the given function with the other geometry's
        # pointer.
        return func(self.ptr, other.ptr)