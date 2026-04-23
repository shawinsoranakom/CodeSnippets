def post_init(self):
        r"""
        Safety checker that arguments are correct - also replaces some NoneType arguments with their default values.
        """
        if not isinstance(self.in_group_size, int):
            raise TypeError("in_group_size must be a float")
        if not isinstance(self.out_group_size, int):
            raise TypeError("out_group_size must be a float")
        if not isinstance(self.num_codebooks, int):
            raise TypeError("num_codebooks must be a float")
        if not isinstance(self.nbits_per_codebook, int):
            raise TypeError("nbits_per_codebook must be a float")

        if self.linear_weights_not_to_quantize is not None and not isinstance(
            self.linear_weights_not_to_quantize, list
        ):
            raise ValueError("linear_weights_not_to_quantize must be a list of strings")

        if self.linear_weights_not_to_quantize is None:
            self.linear_weights_not_to_quantize = []