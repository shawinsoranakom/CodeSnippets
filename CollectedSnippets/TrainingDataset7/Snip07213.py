def _checkdim(self, dim):
        "Check the given dimension."
        if dim < 0 or dim > 3:
            raise GEOSException(f'Invalid ordinate dimension: "{dim:d}"')