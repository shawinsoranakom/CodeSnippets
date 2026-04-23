def post_init(self):
        r"""
        Safety checker that arguments are correct - also replaces some NoneType arguments with their default values.
        """
        if not isinstance(self.bits, int):
            raise TypeError("bits must be an int")
        if not isinstance(self.beta1, int):
            raise TypeError("beta1 must be an int")
        if not isinstance(self.beta2, int):
            raise TypeError("beta2 must be an int")

        if self.bits != 3:
            raise ValueError("SpQR currently only supports bits = 3")
        if self.beta1 != 16:
            raise ValueError("SpQR currently only supports beta1 = 16")
        if self.beta2 != 16:
            raise ValueError("SpQR currently only supports beta2 = 16")
        if not isinstance(self.shapes, dict):
            raise TypeError("shapes must be a dict")