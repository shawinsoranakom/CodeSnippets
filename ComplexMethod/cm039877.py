def _check_params(self):
        if self.type not in (Integral, Real, RealNotInt):
            raise ValueError(
                "type must be either numbers.Integral, numbers.Real or RealNotInt."
                f" Got {self.type} instead."
            )

        if self.closed not in ("left", "right", "both", "neither"):
            raise ValueError(
                "closed must be either 'left', 'right', 'both' or 'neither'. "
                f"Got {self.closed} instead."
            )

        if self.type is Integral:
            suffix = "for an interval over the integers."
            if self.left is not None and not isinstance(self.left, Integral):
                raise TypeError(f"Expecting left to be an int {suffix}")
            if self.right is not None and not isinstance(self.right, Integral):
                raise TypeError(f"Expecting right to be an int {suffix}")
            if self.left is None and self.closed in ("left", "both"):
                raise ValueError(
                    f"left can't be None when closed == {self.closed} {suffix}"
                )
            if self.right is None and self.closed in ("right", "both"):
                raise ValueError(
                    f"right can't be None when closed == {self.closed} {suffix}"
                )
        else:
            if self.left is not None and not isinstance(self.left, Real):
                raise TypeError("Expecting left to be a real number.")
            if self.right is not None and not isinstance(self.right, Real):
                raise TypeError("Expecting right to be a real number.")

        if self.right is not None and self.left is not None and self.right <= self.left:
            raise ValueError(
                f"right can't be less than left. Got left={self.left} and "
                f"right={self.right}"
            )