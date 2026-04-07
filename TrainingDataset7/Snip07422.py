def _construct_ring(
        self,
        param,
        msg=(
            "Parameter must be a sequence of LinearRings or objects that can "
            "initialize to LinearRings."
        ),
    ):
        "Try to construct a ring from the given parameter."
        if isinstance(param, LinearRing):
            return param
        try:
            return LinearRing(param)
        except TypeError:
            raise TypeError(msg)